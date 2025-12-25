import donotuseoriginalboto3 as boto3  # type: ignore
from botocore.exceptions import ClientError, ParamValidationError

from datetime import datetime, timezone
import uuid
import os
import base64
from dataclasses import dataclass, asdict
from typing import Any, Callable, List, Optional
from pathlib import Path

from samsara_fn.commands.runners.env import (
    SamsaraSimulatorConfigDirEnvVar,
    get_env_for_function,
    SamsaraSimulatorRunIdEnvVar,
)
from samsara_fn.commands.utils import get_storage_dir


@dataclass
class FileMetadata:
    """Represents file metadata including last modified time, ETag, and size."""

    LastModified: str
    ETag: str
    Size: int


@dataclass
class S3Object:
    """Represents an S3 object in list responses."""

    Key: str
    LastModified: str
    ETag: str
    Size: int


@dataclass
class ResponseMetadata:
    """Common response metadata for S3 operations."""

    RequestId: str
    HTTPStatusCode: int = 200


@dataclass
class ListObjectsV2Response:
    """Response type for list_objects_v2 operation."""

    ResponseMetadata: ResponseMetadata
    IsTruncated: bool
    NextContinuationToken: Optional[str]
    Contents: List[S3Object]
    Name: str
    Prefix: str
    MaxKeys: int
    EncodingType: str
    KeyCount: int


@dataclass
class PutObjectResponse:
    """Response type for put_object operation."""

    ResponseMetadata: ResponseMetadata
    ETag: str


@dataclass
class DeleteObjectResponse:
    """Response type for delete_object operation."""

    ResponseMetadata: ResponseMetadata
    DeleteMarker: bool = False


@dataclass
class GetObjectResponse:
    """Response type for get_object operation."""

    ResponseMetadata: ResponseMetadata
    LastModified: str
    ETag: str
    ContentLength: int
    ContentType: str = "application/octet-stream"


class StreamingBody:
    """Mimics the behavior of boto3's StreamingBody."""

    def __init__(self, content: bytes):
        self._content = content
        self._position = 0

    def read(self, amt: Optional[int] = None) -> bytes:
        """Read data from the stream.

        Args:
            amt: Number of bytes to read. If None, reads all remaining data.

        Returns:
            The requested bytes.
        """
        if amt is None:
            remaining = self._content[self._position :]
            self._position = len(self._content)
            return remaining

        end = min(self._position + amt, len(self._content))
        data = self._content[self._position : end]
        self._position = end
        return data

    def __iter__(self):
        return self

    def __next__(self):
        data = self.read(1024)
        if not data:
            raise StopIteration()
        return data


def encode_continuation_token(key: str) -> str:
    """Encode a key as a base64 continuation token.

    Args:
        key: The key to encode

    Returns:
        Base64 encoded string
    """
    return base64.b64encode(key.encode()).decode()


def decode_continuation_token(token: str) -> str:
    """Decode a base64 continuation token back to a key.

    Args:
        token: The base64 encoded token

    Returns:
        Decoded key string
    """
    return base64.b64decode(token.encode()).decode()


class MockS3:
    """Mock S3 client that simulates S3 storage behavior.

    This class:
    1. Validates bucket names against expected simulator storage name
    2. Provides local file system-based storage simulation:
       - put_object: Writes files to local storage
       - get_object: Reads files from local storage
       - delete_object: Removes files from local storage
       - list_objects_v2: Lists files with pagination support
    3. Maintains S3-like metadata:
       - LastModified timestamps
       - ETags based on file metadata
       - Content types and lengths
    4. Supports pagination through continuation tokens
    5. Falls back to original S3 client for unexpected buckets
    6. Logs warnings for unexpected method calls

    The mock uses the local file system under .samsara-functions/storage
    to simulate S3 storage, maintaining the same API and behavior as AWS S3.
    """

    def __init__(self, logger, original_client_func: Callable[[], boto3.client]):
        self._logger = logger
        self._original_client_func = original_client_func
        self._original_client = None

    def _use_original(self, name: str) -> Any:
        if self._original_client is None:
            self._original_client = self._original_client_func()
        return getattr(self._original_client, name)

    def __getattr__(self, name: str) -> Any:
        if not name.startswith("__"):
            self._logger.warn(
                f"s3 client called with unexpected method {name}, using the original client"
            )

        return self._use_original(name)

    def list_objects_v2(
        self, Bucket: str, *args: Any, **kwargs: Any
    ) -> ListObjectsV2Response:
        args = parse_list_args(kwargs)

        expected_storage_name = get_env_for_function(
            os.environ[SamsaraSimulatorRunIdEnvVar],
            os.environ[SamsaraSimulatorConfigDirEnvVar],
        )["SamsaraFunctionStorageName"]

        if Bucket != expected_storage_name:
            self._logger.warn(
                f"list_objects_v2 called with unexpected Bucket: {Bucket}, using the original client"
            )
            return self._use_original("list_objects_v2")(Bucket=Bucket, *args, **kwargs)

        storage_dir = Path(get_storage_dir())
        files = []

        # Collect all files with their metadata using pathlib
        for file_path in storage_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(storage_dir)
                # Ensure S3 keys use forward slashes
                key = str(rel_path).replace("\\", "/")
                metadata = get_file_metadata(file_path)
                files.append(
                    S3Object(
                        Key=key,
                        LastModified=metadata.LastModified,
                        ETag=metadata.ETag,
                        Size=metadata.Size,
                    )
                )

        # Sort files by key
        files.sort(key=lambda x: x.Key)

        # Handle pagination
        max_keys = kwargs.get("MaxKeys", 1000)

        # Filter by prefix if specified
        if args.Prefix:
            files = [f for f in files if f.Key.startswith(args.Prefix)]

        # Handle continuation token
        start_idx = 0
        if args.ContinuationToken:
            try:
                decoded_token = decode_continuation_token(args.ContinuationToken)
                start_idx = next(
                    i for i, f in enumerate(files) if f.Key > decoded_token
                )
            except (StopIteration, ValueError):
                start_idx = len(files)

        # Get the requested page of results
        end_idx = min(start_idx + max_keys, len(files))
        page_files = files[start_idx:end_idx]

        # Determine if there are more results
        is_truncated = end_idx < len(files)
        next_token = (
            encode_continuation_token(files[end_idx].Key) if is_truncated else None
        )

        return asdict(
            ListObjectsV2Response(
                ResponseMetadata=ResponseMetadata(RequestId=request_id()),
                IsTruncated=is_truncated,
                NextContinuationToken=next_token,
                Contents=page_files,
                Name=expected_storage_name,
                Prefix=args.Prefix,
                MaxKeys=max_keys,
                EncodingType="url",
                KeyCount=len(page_files),
            )
        )

    def put_object(
        self, Bucket: str, Key: str, Body: Any, *args: Any, **kwargs: Any
    ) -> PutObjectResponse:
        expected_storage_name = get_env_for_function(
            os.environ[SamsaraSimulatorRunIdEnvVar],
            os.environ[SamsaraSimulatorConfigDirEnvVar],
        )["SamsaraFunctionStorageName"]

        if Bucket != expected_storage_name:
            self._logger.warn(
                f"put_object called with unexpected Bucket: {Bucket}, using the original client"
            )
            return self._use_original("put_object")(
                Bucket=Bucket, Key=Key, Body=Body, *args, **kwargs
            )

        storage_dir = Path(get_storage_dir())
        file_path = storage_dir / Key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_bytes(Body)

        return asdict(
            PutObjectResponse(
                ResponseMetadata=ResponseMetadata(RequestId=request_id()),
                ETag=get_file_metadata(file_path).ETag,
            )
        )

    def delete_object(
        self, Bucket: str, Key: str, *args: Any, **kwargs: Any
    ) -> DeleteObjectResponse:
        """Delete an object from the simulated S3 storage.

        Args:
            Bucket: The bucket name (must match SamsaraFunctionStorageName)
            Key: The object key to delete
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            DeleteObjectResponse with metadata about the deletion. Returns 204 status code
            whether the object existed or not, matching AWS S3 behavior.
        """
        expected_storage_name = get_env_for_function(
            os.environ[SamsaraSimulatorRunIdEnvVar],
            os.environ[SamsaraSimulatorConfigDirEnvVar],
        )["SamsaraFunctionStorageName"]

        if Bucket != expected_storage_name:
            self._logger.warn(
                f"delete_object called with unexpected Bucket: {Bucket}, using the original client"
            )
            return self._use_original("delete_object")(
                Bucket=Bucket, Key=Key, *args, **kwargs
            )

        storage_dir = Path(get_storage_dir())
        file_path = storage_dir / Key

        if file_path.exists():
            file_path.unlink()
            # Remove empty directories using pathlib
            try:
                parent = file_path.parent
                while parent != storage_dir and not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
            except OSError:
                pass  # Directory not empty or other error

        # Return 204 No Content whether the object existed or not, matching AWS S3 behavior
        return asdict(
            DeleteObjectResponse(
                ResponseMetadata=ResponseMetadata(
                    RequestId=request_id(), HTTPStatusCode=204
                ),
                DeleteMarker=False,
            )
        )

    def get_object(
        self, Bucket: str, Key: str, *args: Any, **kwargs: Any
    ) -> GetObjectResponse:
        """Get an object from the simulated S3 storage.

        Args:
            Bucket: The bucket name (must match SamsaraFunctionStorageName)
            Key: The object key to retrieve
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            GetObjectResponse with the object's content and metadata

        Raises:
            ClientError: If the object doesn't exist
        """
        expected_storage_name = get_env_for_function(
            os.environ[SamsaraSimulatorRunIdEnvVar],
            os.environ[SamsaraSimulatorConfigDirEnvVar],
        )["SamsaraFunctionStorageName"]

        if Bucket != expected_storage_name:
            self._logger.warn(
                f"get_object called with unexpected Bucket: {Bucket}, using the original client"
            )
            return self._use_original("get_object")(
                Bucket=Bucket, Key=Key, *args, **kwargs
            )

        storage_dir = Path(get_storage_dir())
        file_path = storage_dir / Key

        if not file_path.exists():
            # Simulate AWS S3 behavior by raising a NoSuchKey error
            error = {
                "Error": {
                    "Code": "NoSuchKey",
                    "Message": "The specified key does not exist.",
                    "Key": Key,
                    "RequestId": request_id(),
                }
            }
            raise ClientError(error, "GetObject")

        metadata = get_file_metadata(file_path)
        content = file_path.read_bytes()

        response = asdict(
            GetObjectResponse(
                ResponseMetadata=ResponseMetadata(RequestId=request_id()),
                LastModified=metadata.LastModified,
                ETag=metadata.ETag,
                ContentLength=metadata.Size,
            )
        )
        response["Body"] = StreamingBody(content)
        return response


def request_id() -> str:
    """Generate a unique request ID for S3 operations.

    Returns:
        str: A UUID-based request ID string
    """
    return str(uuid.uuid4())


def get_file_metadata(file_path: Path) -> FileMetadata:
    """Get S3-like metadata for a local file.

    This function:
    1. Gets file size and modification time
    2. Generates an ETag based on file metadata
    3. Formats the last modified time in ISO format

    Args:
        file_path: Path to the local file

    Returns:
        FileMetadata: Object containing S3-like metadata for the file
    """
    stat = file_path.stat()
    return FileMetadata(
        LastModified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        ETag=f"{stat.st_size}_{int(stat.st_mtime * 1000000)}",
        Size=stat.st_size,
    )


@dataclass
class ListArgs:
    Prefix: str
    ContinuationToken: str


def parse_list_args(kwargs: dict[str, Any]) -> ListArgs:
    return ListArgs(
        parse_list_arg("Prefix", kwargs),
        parse_list_arg("ContinuationToken", kwargs),
    )


def parse_list_arg(arg: str, kwargs: dict[str, Any]) -> str:
    value = kwargs.get(arg)
    if value is not None and not isinstance(value, str):
        raise ParamValidationError(
            report=f"Invalid type for parameter {arg}, value: {value}, type: {type(value)}, valid types: <class 'str'>"
        )
    if value is None:
        return ""

    return value
