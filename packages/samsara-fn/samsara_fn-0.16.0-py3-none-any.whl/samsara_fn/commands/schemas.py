import argparse
from dataclasses import dataclass
from pathlib import Path

from .utils import choices_from_dir

from samsara_fn.helptext import description, f


@dataclass
class SchemasArgs:
    """Arguments for schemas command."""

    schema_name: str


def setup_schemas_parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up schemas command parser."""
    schemas_parser = subparsers.add_parser(
        "schemas",
        help="print predefined JSON schemas for validating configuration files",
        description=description(f"""
        {f("View and export predefined JSON schemas for various configuration files used by the simulator.")}

        This command prints the specified JSON schema to standard output (stdout).
        You can redirect this output to a file (e.g., {f("samsara-fn schemas alertPayload > alertPayload.schema.json", "underline")})
        to create a local schema file.

        {f("Using Schemas for Validation:", "bold")}
        These schemas are valuable for validating the structure and data types of your
        JSON configuration files during development, especially when using an IDE or editor
        that supports JSON schema validation.

        To enable validation, you can reference the local schema file within your
        corresponding JSON data file (e.g., your alert payload file) using the {f("$schema", "italic")} key.
        For example, in your {f("my_alert_payload.json", "bright_white")}:
        ```json
        {{
          "$schema": "./alertPayload.schema.json", // Path to your local schema file
          "driverId": "123",
          "assetId": "456",
          // ... other alert payload fields
        }}
        ```

        {f("Important:", "yellow")} The simulator {f("ignores", "bold")} the {f("$schema", "italic")} key during runtime processing
        (e.g., when you use an alert payload file with {f("samsara-fn run alertAction", "underline")}).
        This means you can safely include the {f("$schema", "italic")} key in your JSON files for
        development-time validation without affecting their use with the simulator.

        {f("Arguments:", "yellow")}
        - {f("schema_name", "bold")}: Specifies which schema to output.
          Currently, the available schema is:
          - {f("alertPayload", "italic")}: For validating the structure of alert payload JSON files used with the {f("samsara-fn run alertAction", "underline")} command.

        {f("Example:", "green")}
        {f("samsara-fn schemas alertPayload", "underline")}
        {f("samsara-fn schemas alertPayload > alertPayload.schema.json", "underline")}
        """),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    schemas_parser.add_argument(
        "schema_name",
        help="name of the schema to output to stdout",
        choices=choices_from_dir(
            Path(__file__).parent / ".." / "artifacts" / "schemas",
            filter_func=lambda file: Path(file).name.endswith(".json"),
            map_func=lambda file: Path(file).name.split(".")[0],
        ),
    )


def map_schemas_args(args: argparse.Namespace) -> SchemasArgs:
    """Map schemas arguments to SchemasArgs."""
    return SchemasArgs(
        schema_name=args.schema_name,
    )


def handle_schemas(args: SchemasArgs) -> int:
    schema_path = (
        Path(__file__).parent
        / ".."
        / "artifacts"
        / "schemas"
        / f"{args.schema_name}.json"
    )
    with schema_path.open("r") as f:
        print(f.read())

    return 0
