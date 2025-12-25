from dataclasses import dataclass
from typing import Dict, Callable
import json
import os
import zipfile
import ast
import fnmatch
from pathlib import Path

from samsara_fn.clilogger import logger


def create_temp_directory() -> str:
    """Create a temporary directory for function storage."""
    temp_dir = Path.cwd() / ".samsara-functions"
    temp_dir.mkdir(exist_ok=True)
    return str(temp_dir)


def get_function_dir(func_name: str) -> str:
    """Get the function directory path."""
    temp_dir = create_temp_directory()
    return str(Path(temp_dir) / "functions" / func_name)


def func_name_from_dir(func_dir: str) -> str:
    return Path(func_dir).name


def get_code_dir(func_name: str) -> str:
    return str(Path(get_function_dir(func_name)) / "code")


def get_temp_dir(func_name: str) -> str:
    return str(Path(get_function_dir(func_name)) / "temp")


def get_storage_dir() -> str:
    """Get the function storage directory path."""
    temp_dir = create_temp_directory()
    return str(Path(temp_dir) / "storage")


def cleanup_directory(directory: str, remove_root: bool = True) -> None:
    """Remove existing directory if it exists."""
    dir_path = Path(directory)
    if not dir_path.exists():
        return

    # First, collect all files and directories
    files_to_remove = []
    dirs_to_remove = []

    for item in dir_path.rglob("*"):
        if item.is_file():
            files_to_remove.append(item)
        elif item.is_dir():
            dirs_to_remove.append(item)

    # Remove all files first
    for file_path in files_to_remove:
        try:
            file_path.unlink()
        except Exception as e:
            logger.debug(f"Failed to remove file {file_path}: {str(e)}")

    # Remove directories in reverse order (deepest first)
    for dir_to_remove in sorted(
        dirs_to_remove, key=lambda p: len(p.parts), reverse=True
    ):
        try:
            dir_to_remove.rmdir()
        except Exception as e:
            logger.debug(f"Failed to remove directory {dir_to_remove}: {str(e)}")

    if remove_root:
        try:
            dir_path.rmdir()
            logger.debug(f"Removed existing directory: {directory}")
        except Exception as e:
            logger.debug(f"Failed to remove root directory {directory}: {str(e)}")
    else:
        logger.debug(f"Cleaned up directory: {directory}")


def unzip_package(zip_path: str, extract_path: str) -> None:
    """Unzip the package to the specified path."""
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
    logger.debug(f"Unzipped package to {extract_path}")


def validate_handler(handler: str, code_dir: str) -> bool:
    """Validate that the handler exists and is a valid Python function.

    This function performs several validation checks:
    1. Verifies the handler string format (path.to.file.function_name)
    2. Checks if the specified Python file exists
    3. Validates that the function exists in the file
    4. Ensures the function has exactly two parameters (event and context)

    Args:
        handler: String in format 'path.to.file.function_name'
        code_dir: Directory containing the function code

    Returns:
        bool: True if handler is valid, False otherwise

    Example:
        Valid handler: 'my_module.handlers.process_event'
        This would look for function 'process_event' in 'my_module/handlers.py'
    """
    try:
        if "." not in handler:
            logger.error(
                "Handler must contain at least one dot (.) to separate file path from function name"
            )
            return False

        # Split into file path and function name
        *path_parts, function_name = handler.split(".")
        if not path_parts:
            logger.error("Handler must specify a file path before the function name")
            return False

        # Convert path parts to file path
        file_path = "/".join(path_parts)
        module_file = Path(code_dir) / f"{file_path}.py"

        if not module_file.exists():
            logger.error(f"Handler is invalid, file {module_file} does not exist")
            return False

        with module_file.open("r") as f:
            tree = ast.parse(f.read())

        # Check if the function exists in the module
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # Check that the function has exactly two parameters
                if len(node.args.args) != 2:
                    logger.error(
                        f"Handler function {function_name} must accept exactly two parameters (event and unused context)"
                    )
                    return False
                return True

        logger.error(
            f"Handler is invalid, file {module_file} exists, but function {function_name} does not"
        )
        return False

    except Exception as e:
        logger.error(f"Failed to validate handler: {str(e)}")
        return False


@dataclass
class FunctionConfig:
    """Function configuration structure."""

    handler: str
    parameters: Dict[str, str]
    secrets: Dict[str, str] | str


def load_function_config(func_dir: str) -> FunctionConfig:
    """Load function configuration from config.json."""
    config_path = Path(func_dir) / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Function config not found at {config_path}, try again after initializing the function"
        )

    with config_path.open("r") as f:
        return FunctionConfig(**json.load(f))


def save_function_config(config: FunctionConfig, func_dir: str) -> None:
    """Save function configuration to config.json."""
    config_path = Path(func_dir) / "config.json"
    with config_path.open("w") as f:
        json.dump(config.__dict__, f, indent=2)


def load_gitignore_patterns(gitignore_path: str) -> list[str]:
    """Load gitignore patterns from file."""
    patterns = []
    gitignore_file = Path(gitignore_path)
    if gitignore_file.exists():
        with gitignore_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


def should_ignore(
    gitignore_file_path: str, base_directory: str, file_to_check: str
) -> bool:
    """
    Check if a file should be ignored based on gitignore patterns.

    Args:
        gitignore_file_path: Path to the .gitignore file (can be anywhere)
        base_directory: Base directory to enforce patterns against
        file_to_check: Path to the file/directory to check

    Returns:
        True if the file should be ignored, False otherwise
    """
    patterns = load_gitignore_patterns(gitignore_file_path)

    # Get relative path from base directory
    try:
        base_path = Path(base_directory)
        file_path = Path(file_to_check)
        rel_path = file_path.relative_to(base_path)
    except ValueError:
        # If we can't get relative path, use the file path as is
        rel_path = Path(file_to_check)

    # Normalize path separators for cross-platform compatibility (use forward slashes)
    rel_path_str = str(rel_path).replace("\\", "/")

    for pattern in patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            pattern = pattern.rstrip("/")
            if fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(
                rel_path.name, pattern
            ):
                return True
        # Handle recursive patterns (**)
        elif "**" in pattern:
            # Convert ** patterns to work with fnmatch
            pattern_parts = pattern.split("**")
            if len(pattern_parts) == 2:
                prefix, suffix = pattern_parts
                # Remove leading/trailing slashes
                prefix = prefix.strip("/")
                suffix = suffix.strip("/")

                if not prefix and suffix:
                    # Pattern like **/something - match anywhere
                    # Check if the path contains the suffix as a directory component
                    path_parts = rel_path_str.split("/")
                    if (
                        suffix in path_parts
                        or fnmatch.fnmatch(rel_path_str, f"*/{suffix}")
                        or fnmatch.fnmatch(rel_path_str, suffix)
                    ):
                        logger.debug(f"Ignoring {rel_path_str} because of {pattern}")
                        return True
                    # Also check if any part of the path starts with the suffix (for files inside matching directories)
                    for i, part in enumerate(path_parts):
                        if part == suffix:
                            logger.debug(
                                f"Ignoring {rel_path_str} because of {pattern}"
                            )
                            return True
                elif prefix and not suffix:
                    # Pattern like something/** - match everything under
                    if rel_path_str.startswith(prefix + "/") or rel_path_str == prefix:
                        logger.debug(f"Ignoring {rel_path_str} because of {pattern}")
                        return True
                elif prefix and suffix:
                    # Pattern like prefix/**/suffix
                    if rel_path_str.startswith(prefix + "/") and rel_path_str.endswith(
                        "/" + suffix
                    ):
                        logger.debug(f"Ignoring {rel_path_str} because of {pattern}")
                        return True
        # Handle simple patterns
        else:
            if fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(
                rel_path.name, pattern
            ):
                logger.debug(f"Ignoring {rel_path_str} because of {pattern}")
                return True

    return False


def choices_from_dir(
    dir_path: os.PathLike,
    filter_func: Callable[[str], bool] = lambda x: True,
    map_func: Callable[[str], str] = lambda x: x,
) -> list[str]:
    try:
        path = Path(dir_path)
        dir_contents = [item.name for item in path.iterdir()]
    except FileNotFoundError:
        return []

    choices = []
    for f in dir_contents:
        file_path = path / f

        if filter_func(str(file_path)):
            choices.append(map_func(str(file_path)))

    return sorted(choices)
