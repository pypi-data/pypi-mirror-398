import os
import json
import argparse
from dataclasses import dataclass
from typing import Optional

from samsara_fn.clilogger import logger
from samsara_fn.helptext import description, f
from samsara_fn.commands.utils import (
    get_code_dir,
    get_function_dir,
    cleanup_directory,
    get_storage_dir,
    get_temp_dir,
    unzip_package,
    validate_handler,
    FunctionConfig,
    save_function_config,
)
from samsara_fn.commands.validate import (
    is_one_level_str_dict,
    is_valid_function_name,
    is_valid_secrets_file_name,
)
from .completion import completion


@dataclass
class InitArgs:
    """Arguments for init command."""

    func_name: str
    zipFile: str
    handler: str
    parameters: Optional[str] = None
    secrets: Optional[str] = None


def setup_init_parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up init command parser."""
    init_parser = subparsers.add_parser(
        "init",
        help="initialize a Function locally",
        description=description(f"""
        {f("Initialize a new Samsara Function in your local environment.")}

        Creates a local version of your Function that you can run with the {f("samsara-fn run", "underline")} command.

        This command sets up the necessary directory structure and configuration for a function, mirroring the setup in the Samsara dashboard.
        {f("Important:", "yellow")} Re-running {f("samsara-fn init", "underline")} for an existing function name will overwrite its current local setup.

        {f("Required arguments:", "yellow")}
        - {f("func_name", "bold")}: A unique name for your function.
        - {f("zipFile", "bold")}: Path to the .zip file containing your function's deployment package.
        - {f("handler", "bold")}: The function handler path, similar to AWS Lambda handlers (e.g., {f('"my_module.my_file.my_handler_func"', "italic")}). This specifies the method in your code that the simulator will execute.

        {f("Optional arguments:", "green")}
        - {f("parameters", "bold")}: Path to a JSON file defining runtime parameters. These key-value pairs are passed as part of the {f("event", "italic")} object to your handler function.
        - {f("secrets", "bold")}: Path to a JSON file defining secrets. The filename must start with a dot (e.g., {f('".secrets.json"', "italic")}). Locally, these are made available in a way that mimics AWS SSM; your function can access them using {f("boto3", "italic")} SSM calls. See {f("samsara-fn run --help", "underline")} for details on local secret management during execution.

        Key actions performed:
        - Cleans up any existing local setup for the specified {f("func_name", "italic")} before initializing.
        - Creates a dedicated directory for your function at {f(".samsara-functions/<func_name>", "bright_white")}.
        - Unpacks your function code from the provided .zip file.
        - Generates a {f("config.json", "bright_white")} configuration file with the handler, parameters, and secrets.
        
        The command also performs several important validations:
        - {f("Function Name:", "bold")} Ensures it uses only alphanumeric characters, underscores, or hyphens.
        - {f("Handler Path:", "bold")} Verifies the format ({f('"directory.file.function"', "italic")}), file existence, function presence, and correct function signature (two arguments: event, context).
        - {f("Parameters/Secrets:", "bold")} If JSON files are provided, checks they are flat dictionaries of strings (no nested objects).
        - {f("Secrets File Name:", "bold")} If a secrets file is provided, ensures the filename starts with a dot for security convention.

        To manage Python packages available in the function's runtime environment,
        see the {f("samsara-fn dependencies --help", "underline")} command.

        Use this command to start developing and testing a new function locally.

        {f("Example:", "green")}
        {f("samsara-fn init my-fleet-monitor --zipFile ./my-function.zip --handler fleet.monitor.handler", "underline")}
        {f("samsara-fn init alert-processor --zipFile ./alert-handler.zip --handler alerts.processor.handle_alert --parameters ./params.json --secrets ./.secrets.json", "underline")}
        """),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    comp = completion()

    init_parser.add_argument("func_name", type=str, help="name of the Function")

    init_parser.add_argument(
        "--zipFile",
        "-z",
        type=str,
        required=True,
        help="path to Function code zip file",
        metavar="file/path.zip",
    ).completer = comp.files(["zip"])

    init_parser.add_argument(
        "--handler",
        "-ha",
        type=str,
        required=True,
        help="Function handler path",
        metavar="directory.file.function",
    )

    init_parser.add_argument(
        "--parameters",
        "-p",
        type=str,
        help="path to parameters JSON file",
        metavar="file/path.json",
    ).completer = comp.files(["json"])

    init_parser.add_argument(
        "--secrets",
        "-s",
        type=str,
        help="path to secrets JSON file (filename must start with a dot)",
        metavar="file/.secrets.json",
    ).completer = comp.files(["json"])


def map_init_args(args: argparse.Namespace) -> InitArgs:
    """Map init arguments to InitArgs."""
    return InitArgs(
        func_name=args.func_name,
        zipFile=args.zipFile,
        handler=args.handler,
        parameters=args.parameters,
        secrets=args.secrets,
    )


def handle_init(args: InitArgs) -> int:
    """Handle function initialization."""
    if not is_valid_function_name(args.func_name):
        logger.error(
            f"Invalid function name '{args.func_name}', must contain only alphanumeric characters, underscores, and hyphens"
        )
        return 1

    if len(args.func_name) > 35:
        logger.error(
            f"Function name '{args.func_name}' is too long at {len(args.func_name)} characters, must be less than 36 characters"
        )
        return 1

    # Validate secrets file name if provided
    if args.secrets and not is_valid_secrets_file_name(args.secrets):
        logger.error(
            f"Invalid secrets file name '{args.secrets}'. The filename must start with a dot (e.g., '.secrets.json')"
        )
        return 1

    func_dir = get_function_dir(args.func_name)
    storage_dir = get_storage_dir()
    code_dir = get_code_dir(args.func_name)
    temp_dir = get_temp_dir(args.func_name)

    # Clean up existing function if it exists
    cleanup_directory(func_dir)
    os.makedirs(func_dir, exist_ok=True)
    os.makedirs(storage_dir, exist_ok=True)
    os.makedirs(code_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Unzip the package
        unzip_package(args.zipFile, code_dir)

        # Create function config
        config = FunctionConfig(
            handler=args.handler,
            parameters=json.loads(open(args.parameters, "r").read())
            if args.parameters
            else {},
            secrets=json.loads(open(args.secrets, "r").read())
            if args.secrets
            else "null",
        )

        # Validate that parameters and secrets are string dictionaries
        if not is_one_level_str_dict("Parameters", config.parameters):
            return 1
        if config.secrets != "null" and not is_one_level_str_dict(
            "Secrets", config.secrets
        ):
            return 1

        # Validate the handler
        if not validate_handler(args.handler, code_dir):
            return 1

        save_function_config(config, func_dir)
        logger.debug(f"Function '{args.func_name}' initialized in {func_dir}")
    except Exception as e:
        logger.error(f"Failed to initialize function: {str(e)}")
        return 1

    return 0
