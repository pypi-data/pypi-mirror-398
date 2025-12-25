import donotuseoriginalboto3 as boto3  # type: ignore

from typing import Any, Union

from .mocksts import MockSTS
from .mockssm import MockSSM
from .mocks3 import MockS3

from samsara_fn.clilogger import setup_logger
from samsara_fn.commands.runners.mocks.credentials import (
    do_credentials_match,
    sts_response_credentials_to_client_arguments,
)


class MockBoto3:
    """
    Mock boto3 module that intercepts client creation.

    This class:
    1. Intercepts boto3 client creation for specific services (STS, SSM)
    2. Validates credentials against expected simulator credentials
    3. Provides mock implementations for STS and SSM services
    4. Falls back to original boto3 for unsupported services
    5. Logs warnings for unexpected service or method calls
    """

    def __init__(self):
        self._logger = setup_logger("function")

    def __getattr__(self, name: str) -> Any:
        if not name.startswith("__"):
            self._logger.warn(
                f"boto3 called with unexpected method {name}, returning original"
            )

        return getattr(boto3, name)

    def client(
        self, service_name: str, *args: Any, **kwargs: Any
    ) -> Union[MockSTS, MockSSM, boto3.client]:
        """Create a mock or real boto3 client for the specified service.

        This method:
        1. Validates credentials for non-STS services:
           - Checks for required credential fields
           - Verifies credentials match simulator values
        2. Returns appropriate mock client:
           - MockSTS for STS service
           - MockSSM for SSM service
           - MockS3 for S3 service
        3. Falls back to original boto3 client if:
           - Service is not supported
           - Credentials are missing
           - Credentials don't match simulator values

        Args:
            service_name: Name of the AWS service (e.g., 'sts', 'ssm', 's3')
            *args: Additional positional arguments for client creation
            **kwargs: Additional keyword arguments for client creation

        Returns:
            Union[MockSTS, MockSSM, boto3.client]: Mock client for supported services,
            original boto3 client for unsupported services
        """

        def original_client_func():
            return boto3.client(service_name, *args, **kwargs)

        # Check if credentials are missing
        if service_name != "sts":
            if not all(
                key in kwargs
                for key in sts_response_credentials_to_client_arguments.values()
            ):
                self._logger.error(
                    f"Missing credentials in client creation for {service_name}, using the original client"
                )
                return original_client_func()

            if not do_credentials_match(kwargs):
                self._logger.warn(
                    f"client for {service_name} called with unexpected credentials, using the original client"
                )
                return original_client_func()

        if service_name == "sts":
            return MockSTS(self._logger, original_client_func)
        if service_name == "ssm":
            return MockSSM(self._logger, original_client_func)
        if service_name == "s3":
            return MockS3(self._logger, original_client_func)

        self._logger.warn(
            f"requested an unexpected boto client {service_name}, returning original"
        )
        return original_client_func()
