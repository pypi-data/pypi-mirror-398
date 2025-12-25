import json
import uuid

from samsara_fn.clilogger import logger
from samsara_fn.commands.runners.args import RunArgs
from samsara_fn.commands.utils import load_function_config
from samsara_fn.commands.validate import (
    validate_alert_payload,
    clean_alert_payload,
)
from samsara_fn.commands.runners.env import function_environment


def handle_alert_action_run(args: RunArgs, func_dir: str) -> int:
    """Handle alert action function execution.

    This function:
    1. Loads the function configuration
    2. Validates the alert payload against required schema:
       - Must contain driverId, assetId, and alertConfigurationId
       - All fields must be strings
       - No extra fields allowed (except $schema)
    3. Cleans the payload by removing schema references
    4. Sets up the function environment with alert trigger
    5. Executes the function with alert parameters
    6. Ensures proper cleanup and error handling

    Args:
        args: Command line arguments containing alertPayload path
        func_dir: Directory containing the function code and configuration

    Returns:
        int: 0 on success, 1 on failure (e.g., invalid payload)
    """
    # Load function config
    config = load_function_config(func_dir)

    # Load parameters override if provided
    parameters = config.parameters.copy()
    with open(args.alertPayload, "r") as f:
        alert_payload = json.load(f)

        # Validate alert payload
        is_valid, error_message = validate_alert_payload(alert_payload)
        if not is_valid:
            logger.error(f"Alert payload validation failed: {error_message}")
            return 1

        # Clean and update parameters
        parameters.update(clean_alert_payload(alert_payload))

    runId = str(uuid.uuid4())
    parameters.update({"SamsaraFunctionTriggerSource": "alert"})
    parameters.update({"SamsaraFunctionCorrelationId": runId})

    logger.debug(
        f"Running Function {config.handler} as alert action with runId {runId} and parameters {parameters}"
    )

    with function_environment(runId, config.handler, func_dir) as func:
        return func(parameters, None)
