import json
import re
from pathlib import Path

from typing import Any, Dict, Tuple
from samsara_fn.clilogger import logger


def is_one_level_str_dict(prefix: str, d: dict) -> bool:
    """Check if the dictionary is one level deep with string values."""
    had_error = False
    for k, v in d.items():
        if not isinstance(v, str):
            logger.error(
                f"{prefix} key '{k}' must be just a string, not {type(v).__name__}"
            )
            had_error = True

    return not had_error


def is_valid_function_name(name: str) -> bool:
    """Check if the function name is valid."""
    return re.match(r"^[a-zA-Z0-9_-]+$", name) is not None


def is_valid_secrets_file_name(secrets_path: str) -> bool:
    """Check if the secrets file name starts with a dot.

    Args:
        secrets_path: Path to the secrets file

    Returns:
        bool: True if the filename (not the full path) starts with a dot, False otherwise
    """
    filename = Path(secrets_path).name
    return filename.startswith(".")


def clean_alert_payload(payload: Dict) -> Dict:
    """Remove schema reference from payload."""
    return {k: v for k, v in payload.items() if k != "$schema"}


def load_alert_schema() -> Dict:
    """Load the alert payload JSON schema from the artifacts directory.

    Returns:
        Dict: The parsed JSON schema
    """
    # Find the schema file relative to this module
    schema_path = (
        Path(__file__).parent.parent / "artifacts" / "schemas" / "alertPayload.json"
    )
    with open(schema_path, "r") as f:
        return json.load(f)


def validate_field_type(
    field_name: str, value: Any, expected_type: str
) -> Tuple[bool, str]:
    """Validate that a field value matches the expected type.

    Args:
        field_name: Name of the field being validated
        value: The actual value
        expected_type: The expected JSON schema type (e.g., "string", "number", "boolean")

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    type_mapping = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "object": dict,
        "array": list,
    }

    python_type = type_mapping.get(expected_type)
    if python_type is None:
        return True, ""  # Unknown type, skip validation

    if not isinstance(value, python_type):
        return (
            False,
            f"Field '{field_name}' must be a {expected_type}, got {type(value).__name__}",
        )

    return True, ""


def validate_field_pattern(
    field_name: str, value: str, pattern: str
) -> Tuple[bool, str]:
    """Validate that a string field matches the expected regex pattern.

    Args:
        field_name: Name of the field being validated
        value: The string value to validate
        pattern: The regex pattern to match against

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not isinstance(value, str):
        return True, ""  # Type validation happens separately

    if not re.match(pattern, value):
        return (
            False,
            f"Field '{field_name}' does not match the required pattern: {pattern}",
        )

    return True, ""


def validate_against_schema(payload: Dict, schema: Dict) -> Tuple[bool, str]:
    """Validate a payload against a JSON schema.

    This is a simple schema validator that checks:
    - Required fields are present
    - Field types match the schema
    - Field patterns match (if specified)
    - No extra fields (if additionalProperties is false)
    - Special handling for $schema field

    Args:
        payload: The payload to validate
        schema: The JSON schema to validate against

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Check required fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in payload:
            return False, f"Missing required field: {field}"

    # Get schema properties
    properties = schema.get("properties", {})

    # Validate each field in the payload
    for field_name, field_value in payload.items():
        # Skip $schema field (meta field)
        if field_name == "$schema":
            continue

        # Check if field is allowed
        if field_name not in properties:
            if schema.get("additionalProperties") is False:
                return False, f"Unexpected field: {field_name}"
            continue

        field_schema = properties[field_name]

        # Validate type
        if "type" in field_schema:
            is_valid, error = validate_field_type(
                field_name, field_value, field_schema["type"]
            )
            if not is_valid:
                return False, error

        # Validate pattern (for strings)
        if "pattern" in field_schema and isinstance(field_value, str):
            is_valid, error = validate_field_pattern(
                field_name, field_value, field_schema["pattern"]
            )
            if not is_valid:
                return False, error

    return True, ""


def validate_alert_payload(payload: Dict) -> Tuple[bool, str]:
    """Validate alert payload structure and types using JSON schema.

    This function validates that the alert payload conforms to the JSON schema
    defined in artifacts/schemas/alertPayload.json:
    1. Contains all required fields (driverId, assetId, alertConfigurationId)
    2. Has correct types for all fields (all must be strings)
    3. Matches required patterns (UUID for alertConfigurationId, numeric for IDs)
    4. Does not contain any unexpected fields (except $schema)
    5. Accepts optional fields like alertIncidentTime

    Args:
        payload: Dictionary containing the alert payload to validate

    Returns:
        Tuple[bool, str]:
            - First element is True if payload is valid, False otherwise
            - Second element contains error message if validation fails, empty string if valid

    Example of valid payload:
        {
            "driverId": "123",
            "assetId": "456",
            "alertConfigurationId": "51a1f7de-ca2d-414d-8a23-8e149a4d88be",
            "alertIncidentTime": "1718236800000"
        }
    """
    schema = load_alert_schema()
    return validate_against_schema(payload, schema)
