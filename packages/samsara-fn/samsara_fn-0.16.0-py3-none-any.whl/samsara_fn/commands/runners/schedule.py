import uuid
from samsara_fn.clilogger import logger
from samsara_fn.commands.utils import load_function_config
from samsara_fn.commands.runners.env import function_environment


def handle_schedule_run(func_dir: str):
    """Handle scheduled function execution.

    This function:
    1. Loads the function configuration
    2. Sets up the function environment with schedule trigger
    3. Executes the function with schedule parameters
    4. Ensures proper cleanup and error handling

    Args:
        func_dir: Directory containing the function code and configuration

    Returns:
        int: 0 on success, 1 on failure
    """
    # Load function config
    config = load_function_config(func_dir)

    # Load parameters
    parameters = config.parameters.copy()
    parameters.update({"SamsaraFunctionTriggerSource": "schedule"})

    runId = str(uuid.uuid4())
    parameters.update({"SamsaraFunctionCorrelationId": runId})

    logger.debug(
        f"Running Function {config.handler} on schedule with runId {runId} and parameters {parameters}"
    )

    with function_environment(runId, config.handler, func_dir) as func:
        return func(parameters, None)
