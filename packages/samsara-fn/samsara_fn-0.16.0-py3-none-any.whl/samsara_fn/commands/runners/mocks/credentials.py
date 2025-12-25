import os

from samsara_fn.commands.runners.env import SamsaraSimulatorRunIdEnvVar


def get_mocked_credentials() -> dict:
    """
    Get mock AWS credentials for the simulator.

    Returns:
        Dictionary containing mock access key, secret key, and session token
        with the current run ID embedded in each value.
    """
    run_id = os.environ[SamsaraSimulatorRunIdEnvVar]

    return {
        "AccessKeyId": f"samsara-simulator-access-key-{run_id}",
        "SecretAccessKey": f"samsara-simulator-secret-access-key-{run_id}",
        "SessionToken": f"samsara-simulator-session-token-{run_id}",
    }


sts_response_credentials_to_client_arguments = {
    "AccessKeyId": "aws_access_key_id",
    "SecretAccessKey": "aws_secret_access_key",
    "SessionToken": "aws_session_token",
}


def do_credentials_match(user_credentials: dict) -> bool:
    """
    Check if user-provided credentials exactly match the simulator's mock credentials.

    Args:
        user_credentials: Dictionary of credentials to check against mock values

    Returns:
        True if credentials exactly match mock values (no extra or missing credentials),
        False otherwise
    """
    translated_credentials = {
        sts_response_credentials_to_client_arguments[key]: value
        for key, value in get_mocked_credentials().items()
    }

    # Check if all required credentials are present and match
    if not all(
        translated_credentials.get(key) == user_credentials.get(key)
        for key in translated_credentials.keys()
    ):
        return False

    # Check if there are any extra credentials
    if not all(key in translated_credentials for key in user_credentials.keys()):
        return False

    return True
