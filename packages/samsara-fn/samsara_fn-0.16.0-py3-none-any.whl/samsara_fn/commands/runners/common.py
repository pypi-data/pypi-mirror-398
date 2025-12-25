import json
import uuid
from samsara_fn.commands.runners.args import RunArgs
from samsara_fn.commands.validate import is_one_level_str_dict


def prepare_parameters_with_override(config, trigger_source: str, args: RunArgs):
    """Prepare parameters with trigger source and optional overrides.

    Args:
        config: Function configuration object
        trigger_source: The trigger source to set (e.g., "manual", "api")
        args: Command line arguments containing optional parametersOverride path

    Returns:
        tuple: (parameters_dict, runId, error_code) where error_code is 1 on error, None on success
    """
    parameters = config.parameters.copy()
    parameters.update({"SamsaraFunctionTriggerSource": trigger_source})

    if args.parametersOverride:
        with open(args.parametersOverride, "r") as f:
            override_params = json.load(f)
            if not is_one_level_str_dict("Parameters override", override_params):
                return None, "", 1
            parameters.update(override_params)

    runId = str(uuid.uuid4())
    parameters.update({"SamsaraFunctionCorrelationId": runId})

    return parameters, runId, None
