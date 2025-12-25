import donotuseoriginalboto3 as boto3  # type: ignore

import json
import os
from typing import Any, Callable

from samsara_fn.commands.runners.env import (
    get_env_for_function,
    SamsaraSimulatorRunIdEnvVar,
    SamsaraSimulatorConfigDirEnvVar,
)
from samsara_fn.commands.utils import load_function_config


class MockSSM:
    """
    Mock SSM client that simulates Parameter Store behavior.

    This class:
    1. Validates parameter names against expected simulator path
    2. Returns mock values for simulator parameters
    3. Falls back to original SSM client for unexpected parameters
    4. Logs warnings for unexpected method calls
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
                f"ssm client called with unexpected method {name}, using the original client"
            )

        return self._use_original(name)

    def get_parameter(
        self, Name: str, WithDecryption: bool = False, *args: Any, **kwargs: Any
    ) -> Any:
        expected_parameter_name = get_env_for_function(
            os.environ[SamsaraSimulatorRunIdEnvVar],
            os.environ[SamsaraSimulatorConfigDirEnvVar],
        )["SamsaraFunctionSecretsPath"]

        if Name != expected_parameter_name:
            self._logger.warn(
                f"get_parameter called with unexpected Name: {Name}, using the original client"
            )
            return self._use_original("get_parameter")(
                Name=Name, WithDecryption=WithDecryption, *args, **kwargs
            )

        func_config = load_function_config(os.environ[SamsaraSimulatorConfigDirEnvVar])
        param_value = (
            json.dumps(func_config.secrets) if func_config.secrets != "null" else "null"
        )

        if not WithDecryption:
            param_value = "blahblah"

        return {
            "Parameter": {
                "Value": param_value,
            }
        }
