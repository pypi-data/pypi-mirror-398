import os
from typing import Callable
from contextlib import contextmanager
from samsara_fn.commands.utils import (
    get_code_dir,
    get_temp_dir,
    func_name_from_dir,
)
from samsara_fn.commands.runners.loader import load_handler_module


def filter_python_path(original_path: str) -> str:
    """
    Filter PATH to include only Python and pip related entries.

    This simulates the Lambda environment by keeping only the essential
    Python tooling paths while removing system utilities and user-specific paths.

    Args:
        original_path: The original PATH environment variable

    Returns:
        Filtered PATH containing only Python/pip related entries
    """
    if not original_path:
        return ""

    import os

    # Determine path separator based on OS
    path_separator = ";" if os.name == "nt" else ":"

    # Common Python directories by platform
    common_python_dirs = {
        # Unix/Linux/macOS
        "/usr/bin",
        "/usr/local/bin",
        "/bin",
        "/opt/homebrew/bin",
        # Windows common Python installation paths
        "C:\\Python39",
        "C:\\Python310",
        "C:\\Python311",
        "C:\\Python312",
        "C:\\Python313",
        "C:\\Python39\\Scripts",
        "C:\\Python310\\Scripts",
        "C:\\Python311\\Scripts",
        "C:\\Python312\\Scripts",
        "C:\\Python313\\Scripts",
    }

    python_paths = []
    for path_entry in original_path.split(path_separator):
        # Include paths that contain python or pip in the name
        if any(keyword in path_entry.lower() for keyword in ["python", "pip"]):
            python_paths.append(path_entry)
            continue

        # Include common system directories that contain Python binaries
        if path_entry in common_python_dirs:
            python_paths.append(path_entry)
            continue

        # On Windows, also check for paths that look like Python installations
        if os.name == "nt":
            path_lower = path_entry.lower()
            # Check for typical Windows Python patterns
            if (
                (path_lower.startswith("c:\\users\\") and "python" in path_lower)
                or (
                    path_lower.startswith("c:\\program files")
                    and "python" in path_lower
                )
                or ("appdata" in path_lower and "python" in path_lower)
            ):
                python_paths.append(path_entry)

    return path_separator.join(python_paths)


SamsaraSimulatorRunIdEnvVar = "__DoNotUseSamsaraSimulatorRunId"
SamsaraSimulatorConfigDirEnvVar = "__DoNotUseSamsaraSimulatorConfigDir"


def get_env_for_function(suffix: str, func_dir: str) -> dict:
    """
    Get the environment for a function.

    This function provides a set of environment variables that simulate
    the AWS Lambda and Samsara Functions environment. The suffix parameter
    allows for unique identification of different function executions.

    Only these specified environment variables will be available to the function,
    similar to how AWS Lambda isolates the environment.

    Args:
        suffix: A unique identifier for the function execution

    Returns:
        Dictionary of environment variables
    """
    function_name = func_name_from_dir(func_dir)
    org_id = os.environ.get("SAMSARA_ORG_ID", "1")
    code_path = get_code_dir(function_name)
    temp_storage_path = get_temp_dir(function_name)

    # Filter PATH to include only Python/pip entries to simulate Lambda environment
    original_path = os.environ.get("PATH", "")
    filtered_path = filter_python_path(original_path)

    # AWS specifics
    key_aws_default_region = "AWS_DEFAULT_REGION"
    default_region = os.environ.get(key_aws_default_region, "us-west-2")

    return {
        # System environment (needed for subprocess calls)
        "PATH": filtered_path,
        # AWS Lambda environment
        "AWS_EXECUTION_ENV": f"samsara-functions-simulator-env-{suffix}",
        # Samsara Functions environment
        "SamsaraFunctionExecRoleArn": f"arn:aws:iam::123456789012:role/samsara-functions-simulator-{suffix}",
        "SamsaraFunctionSecretsPath": f"samsara-functions-simulator-secrets-path-{suffix}",
        "SamsaraFunctionStorageName": f"samsara-functions-simulator-storage-name-{suffix}",
        "SamsaraFunctionName": function_name,
        "SamsaraFunctionOrgId": org_id,
        "SamsaraFunctionCodePath": code_path,
        "SamsaraFunctionTempStoragePath": temp_storage_path,
        SamsaraSimulatorRunIdEnvVar: suffix,
        SamsaraSimulatorConfigDirEnvVar: func_dir,
        key_aws_default_region: default_region,
    }


def override_env_for_invocation(env: dict) -> Callable[[], None]:
    """
    Create a function to override environment variables for a function invocation.

    This function:
    1. Removes all existing environment variables
    2. Sets only the specified function-specific environment variables
    3. Returns a cleanup function to restore the original environment

    Args:
        env: Dictionary of environment variables to set

    Returns:
        A cleanup function that restores the original environment
    """
    # Store original environment
    original_env = dict(os.environ)

    def cleanup():
        """Restore the original environment."""
        os.environ.clear()
        os.environ.update(original_env)

    # Clear all existing environment variables
    os.environ.clear()
    # Set only the specified environment variables
    os.environ.update(env)

    return cleanup


@contextmanager
def function_environment(suffix: str, handler: str, func_dir: str):
    """
    Context manager for function environment handling.

    This ensures that:
    1. Only the specified environment variables are present
    2. All other environment variables are removed
    3. Environment is cleaned up after function execution
    4. Cleanup happens even if the function raises an exception
    5. Boto3 services are mocked
    6. Function is loaded within the environment context

    Args:
        suffix: A unique identifier for the function execution
        handler: The handler string in format "path.to.module.function_name"
        func_dir: The absolute path to the function directory

    Yields:
        The loaded function ready to be executed
    """
    cleanup = None

    try:
        # Set up the environment
        env = get_env_for_function(suffix, func_dir)
        cleanup = override_env_for_invocation(env)

        # Load the function with our mock
        code_dir = get_code_dir(func_dir)
        func = load_handler_module(handler, code_dir)

        yield func
    finally:
        # Always clean up the environment
        if cleanup:
            cleanup()
