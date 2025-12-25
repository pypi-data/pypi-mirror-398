from samsara_fn.clilogger import logger
from samsara_fn.commands.runners.args import RunArgs
from samsara_fn.commands.utils import load_function_config
from samsara_fn.commands.runners.env import function_environment
from samsara_fn.commands.runners.common import prepare_parameters_with_override


def handle_api_run(args: RunArgs, func_dir: str):
    """Handle API function execution.

    This function:
    1. Loads the function configuration
    2. Handles parameter overrides:
       - Starts with base parameters from config
       - Adds API trigger source
       - Applies any parameter overrides from file
       - Validates that all parameters are string values
    3. Sets up the function environment:
       - Creates unique run ID
       - Configures environment variables
       - Installs boto3 mocks
    4. Executes the function with parameters
    5. Ensures proper cleanup of environment

    Args:
        args: Command line arguments containing optional parametersOverride path
        func_dir: Directory containing the function code and configuration

    Returns:
        The function's return value or 1 on error
    """
    # Load function config
    config = load_function_config(func_dir)

    # Prepare parameters with override
    parameters, runId, error = prepare_parameters_with_override(config, "api", args)
    if error:
        return error

    logger.debug(
        f"Running Function {config.handler} via API with runId {runId} and parameters {parameters}"
    )

    with function_environment(runId, config.handler, func_dir) as func:
        return func(parameters, None)
