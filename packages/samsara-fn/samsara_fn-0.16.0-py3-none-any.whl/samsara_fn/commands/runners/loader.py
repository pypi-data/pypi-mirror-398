import importlib
import importlib.util
import importlib.machinery
import importlib.abc
import sys
from contextlib import contextmanager
from pathlib import Path


class FunctionImportFinder(importlib.abc.MetaPathFinder):
    """
    Custom import finder that looks for modules in the function directory.

    This class implements Python's import hook system to handle module imports
    within the function's directory. It's used to ensure that:
    1. Modules can be imported from the function directory
    2. Imports are isolated to the specific function being loaded
    3. Standard library imports still work normally
    4. Relative imports within the function directory work correctly
    5. Package imports (directories with __init__.py) work correctly
    6. Nested module paths are handled properly

    The finder is added to sys.meta_path temporarily during function loading
    and removed afterward to prevent affecting other functions or the system.
    """

    def __init__(self, func_dir: Path):
        """
        Initialize the finder with the function directory.

        Args:
            func_dir: The path to the function directory where modules
                     should be searched for.
        """
        self.func_dir = Path(func_dir)
        # Track loaded modules to handle import caching
        self._loaded_modules = {}

    def _find_module_path(self, fullname: str, path: Path) -> tuple[Path | None, bool]:
        """
        Find the actual path to a module, handling both files and packages.

        Args:
            fullname: The full module name (e.g., 'utils.helpers.common')
            path: The base path to search in

        Returns:
            Tuple of (module_path, is_package) or (None, False) if not found
        """
        # Split the module name into parts
        parts = fullname.split(".")

        # Start with the base path
        current_path = Path(path)

        # Walk through the module path parts
        for i, part in enumerate(parts):
            # Check for a package directory
            package_dir = current_path / part
            init_file = package_dir / "__init__.py"

            if init_file.exists():
                # This is a package directory
                current_path = package_dir
                if i == len(parts) - 1:
                    # This is the final part, so it's the package we're looking for
                    return init_file, True
                continue

            # Check for a module file
            module_file = current_path / f"{part}.py"
            if module_file.exists():
                if i == len(parts) - 1:
                    # This is the final part, so it's the module we're looking for
                    return module_file, False
                # This is a module but we need to go deeper, which is invalid
                return None, False

            # Neither a package nor a module found at this level
            return None, False

    def find_spec(self, fullname, path, target=None):
        """
        Find the module spec in the function directory.

        This method is called by Python's import system when a module is being
        imported. It will:
        1. Look for the module in the function directory
        2. Handle both package and module imports
        3. Support nested module paths
        4. Handle import caching

        Edge cases handled:
        - Empty path entries (skipped)
        - Non-existent modules (returns None)
        - Nested module paths (handles full path)
        - Relative imports (path is provided)
        - Package imports (directories with __init__.py)
        - Import caching (tracks loaded modules)

        Args:
            fullname: The full name of the module being imported
            path: The path to search in (None for top-level imports)
            target: The target module (if any)

        Returns:
            ModuleSpec if found, None otherwise
        """
        if path is None:
            path = [self.func_dir]

        # Check if we've already loaded this module
        if fullname in self._loaded_modules:
            return self._loaded_modules[fullname]

        # Try to find the module in the function directory
        for entry in path:
            if not entry:
                continue

            module_path, is_package = self._find_module_path(fullname, Path(entry))
            if module_path:
                # Create the spec
                spec = importlib.util.spec_from_file_location(
                    fullname,
                    str(module_path),
                    submodule_search_locations=[str(module_path.parent)]
                    if is_package
                    else None,
                )

                # Cache the spec
                self._loaded_modules[fullname] = spec
                return spec

        return None


@contextmanager
def function_import_context(code_dir: str):
    """
    Context manager that adds function directory to import path and installs boto3 mock.

    This context manager ensures that:
    1. The import finder is added at the start of sys.meta_path (highest priority)
    2. The boto3 mock is installed before any imports happen
    3. The finder is properly removed after the function is loaded
    4. The import system is restored to its original state even if an error occurs
    5. Import caching is handled correctly

    Args:
        code_dir: The absolute path to the code directory
    """
    # Store original boto3 module and set up the mock module name
    import boto3

    original_boto3 = boto3
    sys.modules["donotuseoriginalboto3"] = original_boto3

    # Create the finder and add it to meta_path
    finder = FunctionImportFinder(Path(code_dir))
    sys.meta_path.insert(0, finder)

    try:
        # Now we can safely import the mock module
        import samsara_fn.commands.runners.mocks.mockboto3 as mockboto3

        sys.modules["boto3"] = mockboto3.MockBoto3()
        yield
    finally:
        # Always remove the finder, even if an error occurs
        sys.meta_path.remove(finder)
        # Clear any modules we loaded from sys.modules
        for module_name in list(sys.modules.keys()):
            if module_name in finder._loaded_modules:
                del sys.modules[module_name]
        # Restore original boto3
        if sys.modules["donotuseoriginalboto3"]:
            sys.modules["boto3"] = sys.modules["donotuseoriginalboto3"]

        del sys.modules["donotuseoriginalboto3"]


def load_handler_module(handler: str, code_dir: str):
    """
    Load the handler module from the function directory.

    This function:
    1. Parses the handler string to get module path and function name
    2. Sets up the import context for the function directory
    3. Loads the module and returns the specified function

    Args:
        handler: The handler string in format "path.to.module.function_name"
        code_dir: The absolute path to the code directory

    Returns:
        The function object from the module
    """
    # Split handler into module path and function name
    *path_parts, function_name = handler.split(".")
    module_path = "/".join(path_parts)
    module_file = Path(code_dir) / f"{module_path}.py"

    if not module_file.exists():
        raise FileNotFoundError(
            f"Handler module not found at {module_file}, try again after initializing the function"
        )

    # Load the module within the import context
    with function_import_context(code_dir):
        spec = importlib.util.spec_from_file_location(
            module_path.replace("/", "."), str(module_file)
        )

        if spec is None:
            raise ImportError(
                f"Failed to load module from {module_file}, try again after initializing the function"
            )

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get the function
        if not hasattr(module, function_name):
            raise AttributeError(
                f"Function {function_name} not found in module, try again after initializing the function"
            )

        return getattr(module, function_name)
