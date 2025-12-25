import donotuseoriginalboto3 as boto3  # type: ignore

import os
from typing import Any, Callable

from samsara_fn.commands.runners.env import (
    get_env_for_function,
    SamsaraSimulatorRunIdEnvVar,
    SamsaraSimulatorConfigDirEnvVar,
)
from samsara_fn.commands.runners.mocks.credentials import (
    get_mocked_credentials,
)


class MockSTS:
    """
    Mock STS client that simulates Security Token Service behavior.

    This class:
    1. Validates role ARN and session name against simulator values
    2. Returns mock credentials for simulator role assumptions
    3. Falls back to original STS client for unexpected roles
    4. Logs warnings for unexpected method calls
    """

    def __init__(self, logger, original_client_func: Callable[[], boto3.client]):
        self._original_client_func = original_client_func
        self._logger = logger
        self._original_client = None

    def _use_original(self, name: str) -> Any:
        if self._original_client is None:
            self._original_client = self._original_client_func()
        return getattr(self._original_client, name)

    def __getattr__(self, name: str) -> Any:
        if not name.startswith("__"):
            self._logger.warn(
                f"sts client called with unexpected method {name}, using the original client"
            )

        return self._use_original(name)

    def assume_role(
        self, RoleArn: str, RoleSessionName: str, *args: Any, **kwargs: Any
    ) -> Any:
        current_env = get_env_for_function(
            os.environ[SamsaraSimulatorRunIdEnvVar],
            os.environ[SamsaraSimulatorConfigDirEnvVar],
        )

        expected_role_arn = current_env["SamsaraFunctionExecRoleArn"]
        expected_role_session_name = current_env["SamsaraFunctionName"]

        if (
            RoleArn != expected_role_arn
            or RoleSessionName != expected_role_session_name
        ):
            self._logger.warn(
                f"assume_role called with unexpected RoleArn {RoleArn}, RoleSessionName {RoleSessionName}, using the original client"
            )
            return self._use_original("assume_role")(
                RoleArn=RoleArn, RoleSessionName=RoleSessionName, *args, **kwargs
            )

        return {
            "Credentials": get_mocked_credentials(),
        }
