import argparse
import os
from dataclasses import dataclass
import subprocess
import shutil
import tempfile
import zipfile
import re
from pathlib import Path

from .completion import completion

from .utils import should_ignore

from samsara_fn.helptext import description, f
from samsara_fn.clilogger import logger


@dataclass
class BundleArgs:
    """Arguments for bundle command."""

    directory: str
    ignore_file: str
    include_all: bool
    output_dir: str
    do_prod_vendor: bool
    zip_name: str


def setup_bundle_parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up bundle command parser."""
    bundle_parser = subparsers.add_parser(
        "bundle",
        help="bundle a source directory into a zip file",
        description=description(f"""
        {f("Create a deployment-ready zip file from a source directory.")}

        This command packages your function code and dependencies into a zip file suitable
        for use with the {f("samsara-fn init", "underline")} command. It applies intelligent filtering
        to exclude common development artifacts and potentially sensitive files, helping you
        create clean, secure deployment packages.

        {f("Usage with Init Command:", "green")}
        The generated zip file can be directly used as the {f("--zipFile", "italic")} argument when
        initializing a function with {f("samsara-fn init", "underline")}. This creates a complete
        workflow: bundle your source code, then initialize it as a local function for testing.

        {f("Required arguments:", "yellow")}
        - {f("input_directory", "bold")}: Path to the directory containing your function code to bundle.
        - {f("output_directory", "bold")}: Path to the directory where the zip file will be placed.

        {f("Optional arguments:", "green")}
        - {f("ignore_file", "bold")}: Path to a custom ignore file for filtering. If not specified, uses the default ignore patterns that exclude {f("__pycache__", "italic")} directories and common hidden/system files.
        - {f("include_all", "bold")}: Include all files without any filtering. Use with caution as this bypasses security warnings for sensitive files.
        - {f("do_prod_vendor", "bold")}: Run the production vendoring script, if present, before bundling. Detects the script based on the additional-python-dependencies template. If the script is not present, it is ignored. Returns the previous state of the generated lib folder afterwards.
        - {f("zip_name", "bold")}: Name of the zip file to create, including extension. If not specified, uses the directory name and .zip extension.
        
        Key actions performed:
        - Walks through all files in the specified directory.
        - Applies filtering based on ignore patterns (unless {f("--include-all", "italic")} is specified).
        - Warns about potentially sensitive files (e.g., {f(".env", "italic")}, {f("*.key", "italic")}, {f("*secret*", "italic")}) and large files (configurable via {f("SAMSARA_SIMULATOR_LARGE_FILE_SIZE_MB", "bright_white")} environment variable, defaults to 1.0 MB).
        - Creates a zip file named {f("<directory_name>.zip", "bright_white")} in the specified output location.
        - Provides a summary of files added, skipped, and warnings generated.

        {f("Security Considerations:", "yellow")}
        The command automatically detects and warns about files that might contain sensitive information:
        - Environment files ({f(".env", "italic")}, {f(".env.*", "italic")})
        - Key files ({f("*.key", "italic")}, {f("*.pem", "italic")}, {f("*.p12", "italic")}, {f("*.pfx", "italic")})
        - Configuration files that might contain credentials
        - SSH and AWS credential directories

        {f("Important:", "yellow")} 
        Review all warnings carefully before using the generated zip file.
        If sensitive or large files are flagged, you can either remove them from your source directory
        and re-run the bundle command, or create a custom ignore file (in {f(".gitignore", "italic")} format)
        using the {f("--ignore-file", "italic")} option to exclude them from bundling.

        {f("Example:", "green")}
        {f("samsara-fn bundle ./my-function .", "underline")}
        {f("samsara-fn bundle ./my-function ./dist", "underline")}
        {f("samsara-fn bundle ./my-function . --ignore-file ./.bundleignore", "underline")}
        
        {f("Complete Workflow Example:", "green")}
        {f("samsara-fn bundle ./my-function .", "underline")}
        {f("samsara-fn init my-function --zipFile ./my-function.zip --handler main.handler", "underline")}
        """),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    comp = completion()

    bundle_parser.add_argument(
        "input_directory",
        help="path to the directory to bundle",
    ).completer = comp.directories

    bundle_parser.add_argument(
        "output_directory",
        help="path to the directory where the zip file will be placed",
    ).completer = comp.directories

    bundle_parser.add_argument(
        "--include-all",
        "-a",
        action="store_true",
        help="include all files in the directory, without suggested filtering",
    )

    bundle_parser.add_argument(
        "--ignore-file",
        "-i",
        help="path to the ignore file to use for filtering",
        metavar="/path/ignore.txt",
    ).completer = comp.files(["txt", "ignore", "gitignore"])

    bundle_parser.add_argument(
        "--do-prod-vendor",
        "-pv",
        action="store_true",
        help="run the production vendoring script, before bundling",
    )

    bundle_parser.add_argument(
        "--zip-name",
        "-z",
        help="name of the zip file to create",
        metavar="prod.zip",
    )


def map_bundle_args(args: argparse.Namespace) -> BundleArgs:
    """Map bundle arguments to BundleArgs."""
    return BundleArgs(
        directory=args.input_directory,
        ignore_file=args.ignore_file,
        include_all=args.include_all,
        output_dir=args.output_directory,
        do_prod_vendor=args.do_prod_vendor,
        zip_name=args.zip_name,
    )


def get_large_file_threshold() -> float:
    """Get the large file size threshold in MB from environment variable or default."""
    try:
        return float(os.environ.get("SAMSARA_SIMULATOR_LARGE_FILE_SIZE_MB", "1.0"))
    except ValueError:
        logger.warning(
            "Invalid SAMSARA_SIMULATOR_LARGE_FILE_SIZE_MB value, using default 1.0 MB"
        )
        return 1.0


def is_potentially_sensitive_file(file_path: str) -> bool:
    """Check if a file might contain sensitive information."""
    sensitive_patterns = [
        r".*\.env$",
        r".*\.env\..*",
        r".*secret.*",
        r".*password.*",
        r".*\.key$",
        r".*\.pem$",
        r".*\.p12$",
        r".*\.pfx$",
        r".*config.*\.json$",
        r".*credentials.*",
        r".*\.aws/.*",
        r".*\.ssh/.*",
    ]

    filename = Path(file_path).name.lower()
    for pattern in sensitive_patterns:
        if re.match(pattern, filename):
            return True
    return False


def should_warn_about_file(file_path: str, max_size_mb: float) -> tuple[bool, str]:
    """Check if we should warn about a file and return the reason."""
    try:
        if is_potentially_sensitive_file(file_path):
            return (
                True,
                "Potentially sensitive file, are you sure you need to include it?",
            )

        file_size = Path(file_path).stat().st_size
        size_mb = file_size / (1024 * 1024)

        if size_mb > max_size_mb:
            return (
                True,
                f"File is large ({size_mb:.1f}MB), are you sure you need to include it?",
            )

    except OSError:
        return True, "Cannot access file"

    return False, ""


def handle_bundle(args: BundleArgs) -> int:
    """Handle the bundle command."""
    ignore_file_path = (
        Path(__file__).parent / ".." / "artifacts" / "bundle" / "ignore.txt"
    )

    if args.ignore_file:
        ignore_file_path = Path(args.ignore_file)
        if not ignore_file_path.is_file():
            logger.error(f"Ignore file '{ignore_file_path}' does not exist")
            return 1

        logger.info(f"Using custom ignore file: {ignore_file_path}")

    directory_path = Path(args.directory)
    if not directory_path.is_dir():
        logger.error(f"Directory '{args.directory}' does not exist")
        return 1

    # Get configurable file size threshold
    max_file_size_mb = get_large_file_threshold()
    logger.debug(f"Large file threshold: {max_file_size_mb} MB")

    restore_lib_path = None
    if args.do_prod_vendor:
        script_path = directory_path / "run-before-bundle" / "install_deps_to_lib.py"
        if script_path.is_file():
            logger.info(f"Running production vendoring script at '{script_path}'")

            original_lib_path = directory_path / "lib"
            if original_lib_path.exists():
                temp_lib_path = tempfile.mkdtemp(prefix="samsara-fn-bundle")
                shutil.copytree(original_lib_path, temp_lib_path, dirs_exist_ok=True)

                def restore():
                    shutil.rmtree(original_lib_path, ignore_errors=True)
                    shutil.copytree(
                        temp_lib_path, original_lib_path, dirs_exist_ok=True
                    )

                restore_lib_path = restore

            subprocess.run(["python", script_path, "prod"], check=True)
        else:
            logger.warning(f"Vendoring script '{script_path}' does not exist, skipping")

    # Create output zip file name
    dir_name = directory_path.resolve().name
    zip_filename = f"{dir_name}.zip"
    if args.zip_name:
        zip_filename = args.zip_name

    zip_path = Path.cwd() / zip_filename
    if args.output_dir:
        output_dir = Path(args.output_dir)
        if not output_dir.is_dir():
            logger.debug(f"Creating output directory {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)

        zip_path = output_dir / zip_filename

    # Remove existing zip file if it exists
    if zip_path.exists():
        zip_path.unlink()
        logger.info(f"Removed existing {zip_filename}")

    files_added = 0
    files_skipped = 0
    warnings_count = 0
    total_dir_size = 0  # Track total size of files being bundled

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Walk through all files in the directory
            for file_path in directory_path.rglob("*"):
                if file_path.is_file():
                    # Add to total directory size before any filtering
                    try:
                        total_dir_size += file_path.stat().st_size
                    except OSError:
                        # Skip files we can't access
                        pass

                    # Check if file should be ignored (unless include_all is set)
                    if not args.include_all and should_ignore(
                        str(ignore_file_path), args.directory, str(file_path)
                    ):
                        files_skipped += 1
                        logger.debug(f"{file_path}: Skipped (ignored)")
                        continue

                    # Check for warnings about the file
                    should_warn, reason = should_warn_about_file(
                        str(file_path), max_file_size_mb
                    )
                    if should_warn:
                        warnings_count += 1
                        logger.warning(f"{file_path}: Bundled with warning: {reason}")
                    else:
                        logger.debug(f"{file_path}: Bundled")

                    # Calculate relative path for the zip archive
                    arcname = file_path.relative_to(directory_path)

                    # Add file to zip
                    try:
                        zipf.write(file_path, arcname)
                        files_added += 1
                    except Exception as e:
                        logger.error(f"Failed to add {file_path}: {str(e)}")
                        return 1

        # Calculate sizes in MB
        dir_size_mb = total_dir_size / (1024 * 1024)
        zip_size_mb = zip_path.stat().st_size / (1024 * 1024)

        # Calculate unzipped size by reading zip file info
        unzipped_size = 0
        with zipfile.ZipFile(zip_path, "r") as zipf:
            for info in zipf.infolist():
                if not info.is_dir():  # Only count files, not directories
                    unzipped_size += info.file_size
        unzipped_size_mb = unzipped_size / (1024 * 1024)

        if restore_lib_path:
            restore_lib_path()
            logger.info("Restored original lib directory after production vendoring")

        # Summary
        logger.info(
            f"Bundle created: {zip_filename} ({files_added} files, {files_skipped} skipped, {warnings_count} warnings) ({dir_size_mb:.1f} MB raw, {zip_size_mb:.1f} MB zipped, {unzipped_size_mb:.1f} MB unzipped)"
        )

        return_code = 0
        MAX_ZIPPED_SIZE_MB = 14.5
        if zip_size_mb > MAX_ZIPPED_SIZE_MB:
            logger.error(
                f"The zipped bundle is too large and will not be able to be uploaded to Samsara Functions (max {MAX_ZIPPED_SIZE_MB} MB)"
            )
            return_code = 1

        MAX_UNZIPPED_SIZE_MB = 200
        if unzipped_size_mb > MAX_UNZIPPED_SIZE_MB:
            logger.error(
                f"The unzipped bundle is too large and will not be able to be uploaded to Samsara Functions (max {MAX_UNZIPPED_SIZE_MB} MB)"
            )
            return_code = 1

        logger.info("Run 'samsara-fn --verbose bundle' to see more details.")

        return return_code

    except Exception as e:
        logger.error(f"Failed to create bundle: {str(e)}")
        return 1
