import json
import argparse
from pathlib import Path

from samsara_fn.helptext import description, f
from samsara_fn.clilogger import logger
from samsara_fn.commands.runners.alert import handle_alert_action_run
from samsara_fn.commands.runners.manual import handle_manual_run
from samsara_fn.commands.runners.schedule import handle_schedule_run
from samsara_fn.commands.runners.api import handle_api_run
from samsara_fn.commands.runners.args import RunArgs
from samsara_fn.commands.utils import (
    cleanup_directory,
    choices_from_dir,
    get_function_dir,
    get_temp_dir,
)
from .completion import completion


def setup_func_name_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "func_name",
        help="name of the Function",
        choices=choices_from_dir(
            Path.cwd() / ".samsara-functions" / "functions",
            filter_func=lambda file: Path(file).is_dir(),
            map_func=lambda file: Path(file).name,
        ),
    )


def setup_run_parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up run command parser."""
    run_parser = subparsers.add_parser(
        "run",
        help="execute a previously initialized Function locally",
        description=description(f"""
        {f("Execute a previously initialized Samsara Function in your local environment.")}

        This command allows you to simulate the various ways a function can be invoked
        in the Samsara cloud, helping you test its behavior with different inputs and
        configurations before deployment. It requires the function to have been previously
        set up using the {f("samsara-fn init --help", "underline")} command.

        {f("Important:", "yellow")} In the production environment, functions must complete execution
        within 15 minutes or they will be abruptly terminated. The simulator tool does not
        enforce this time limit, so ensure your function logic is designed to complete
        within this constraint.

        The {f("run", "italic")} command has four distinct modes of operation, each invoked as a subcommand:
        - {f("manual:", "bold")} For direct invocations with optional parameter overrides.
          (See {f("samsara-fn run manual --help", "underline")})
        - {f("api:", "bold")} To simulate an API invocation with optional parameter overrides.
          (See {f("samsara-fn run api --help", "underline")})
        - {f("alertAction:", "bold")} To simulate an invocation triggered by a Samsara alert, using an alert payload.
          (See {f("samsara-fn run alertAction --help", "underline")})
        - {f("schedule:", "bold")} To simulate a scheduled invocation.
          (See {f("samsara-fn run schedule --help", "underline")})

        {f("Function Environment & AWS SDK Stubbing:", "bold")}
        The function executes in an isolated environment with predefined environment variables.
        Interactions with the AWS SDK ({f("boto3", "italic")}) are partially stubbed:

        {f("Supported boto3 Clients & Methods:", "green")}
        - {f("STS (sts):", "italic")}
          - {f("assume_role:", "bold")} Mocked to return simulator-specific credentials if {f("RoleArn", "italic")} (from {f("SamsaraFunctionExecRoleArn", "italic")} env var) and {f("RoleSessionName", "italic")} (from {f("SamsaraFunctionName", "italic")} env var) match.
        - {f("SSM (ssm):", "italic")}
          - {f("get_parameter:", "bold")} Mocked to return secrets defined in {f("config.json", "bright_white")} if {f("Name", "italic")} matches the {f("SamsaraFunctionSecretsPath", "italic")} env var. The {f("WithDecryption=True", "italic")} flag is respected.
        - {f("S3 (s3):", "italic")}
          - {f("put_object, get_object, delete_object, list_objects_v2:", "bold")} Mocked to interact with the local {f(".samsara-functions/storage/", "bright_white")} directory if the {f("Bucket", "italic")} name matches the {f("SamsaraFunctionStorageName", "italic")} env var.

        {f("Behavior for Unstubbed AWS SDK Calls:", "yellow")}
        - If your function attempts to use a {f("boto3", "italic")} client other than {f("sts", "italic")}, {f("ssm", "italic")}, or {f("s3", "italic")} (e.g., {f("boto3.client('sqs')", "italic")}), the simulator will use the original {f("boto3", "italic")} client, allowing real AWS calls if credentials are configured. A warning will be logged.
        - If a method is called on a supported client ({f("sts", "italic")}, {f("ssm", "italic")}, {f("s3", "italic")}) that is not explicitly stubbed (e.g., {f("ssm.put_parameter()", "italic")}), or if parameters for a stubbed method do not match expectations (e.g., wrong {f("RoleArn", "italic")}), the call will be delegated to the original {f("boto3", "italic")} client. A warning will be logged.
        - Ensure your function's AWS SDK calls use credentials obtained via the stubbed {f("sts.assume_role", "italic")} for consistent local behavior, especially for {f("s3", "italic")} and {f("ssm", "italic")} interactions.

        {f("Standard Environment Variables:", "green")}
        Your function can access the following environment variables during local execution:
        - {f("SamsaraFunctionExecRoleArn", "bold")}: ARN for role assumption.
        - {f("SamsaraFunctionSecretsPath", "bold")}: Path for SSM {f("get_parameter", "italic")}.
        - {f("SamsaraFunctionStorageName", "bold")}: Bucket name for S3.
        - {f("SamsaraFunctionName", "bold")}: The name of your function.
        - {f("SamsaraFunctionOrgId", "bold")}: Your organization ID. This defaults to "1" but can be overridden by setting the {f("SAMSARA_ORG_ID", "bright_white")} environment variable in your shell before running the simulator.
        - {f("SamsaraFunctionCodePath", "bold")}: Filesystem path to your function's code (the contents of the .zip file provided during {f("init", "italic")}). Use this to access any bundled files.
        - {f("SamsaraFunctionTempStoragePath", "bold")}: Filesystem path to a temporary directory for your function. This directory is cleared before each run and is available only for the duration of a single execution. Its contents can be inspected after a run for debugging at {f(".samsara-functions/functions/<func_name>/temp", "bright_white")}.

        {f("Event Parameter:", "green")}
        The {f("event", "italic")} parameter is the first argument passed to your function handler. It is a one-level dictionary containing string values that can be accessed like any Python dictionary (e.g., {f("event['SamsaraFunctionTriggerSource']", "italic")} or {f("event.get('parameter_name')", "italic")}). The contents of this dictionary vary depending on the invocation mode and include parameters from {f("config.json", "bright_white")}, trigger-specific data, and metadata about the function execution.

        Function logs are printed to the console. Any return value from the function is
        printed to STDOUT as JSON (if serializable).
        {f("Important:", "yellow")} Function return values are ignored in the production environment;
        a warning log will be issued by the simulator if your function returns a value.
        """),
        formatter_class=argparse.RawTextHelpFormatter,  # Will be CustomHelpFormatter
    )
    run_subparsers = run_parser.add_subparsers(dest="run_command", required=True)

    # manual run
    manual_parser = run_subparsers.add_parser(
        "manual",
        help="execute the function with a direct, manual invocation",
        description=description(f"""
        {f("Manually invoke an initialized Samsara Function.")}

        This mode simulates a direct execution of your function. The {f("event", "italic")} object passed
        to your handler will include a {f("SamsaraFunctionTriggerSource", "italic")} key set to {f('"manual"', "italic")}.
        You can optionally provide a JSON file to override the default parameters
        defined during {f("samsara-fn init", "underline")}.

        {f("Required arguments:", "yellow")}
        - {f("func_name", "bold")}: The name of the function (must have been initialized).

        {f("Optional arguments:", "green")}
        - {f("parametersOverride", "bold")}: Path to a JSON file. If provided, these key-value pairs will override the parameters stored in {f("config.json", "bright_white")} for this specific run. The override is a flat dictionary of strings.

        {f("Example:", "green")}
        {f("samsara-fn run manual my-fleet-monitor", "underline")}
        {f("samsara-fn run manual my-fleet-monitor --parametersOverride ./test-params.json", "underline")}
        """),
        formatter_class=argparse.RawTextHelpFormatter,  # Will be CustomHelpFormatter
    )
    setup_func_name_arg(manual_parser)

    comp = completion()
    manual_parser.add_argument(
        "--parametersOverride",
        "-po",
        type=str,
        help="path to parameters override JSON file",
        metavar="file/path.json",
    ).completer = comp.files(["json"])

    # alert action run
    alert_parser = run_subparsers.add_parser(
        "alertAction",
        help="simulate a function invocation triggered by a Samsara alert",
        description=description(f"""
        {f("Simulate a Samsara Function invocation in response to a Platform Alert, which can be configured in the Samsara dashboard.")}

        This mode tests how your function processes alert data. You must provide a JSON file
        representing the alert payload. The {f("event", "italic")} object passed to your handler will
        include a {f("SamsaraFunctionTriggerSource", "italic")} key set to {f('"alert"', "italic")}, the alert payload
        data, and any parameters from {f("config.json", "bright_white")}.
        For the expected structure of the alert payload, see {f("samsara-fn schemas --help", "underline")}.

        {f("Required arguments:", "yellow")}
        - {f("func_name", "bold")}: The name of the function (must have been initialized).
        - {f("alertPayload", "bold")}: Path to a JSON file containing the alert payload data.

        {f("Example:", "green")}
        {f("samsara-fn run alertAction my-alert-handler --alertPayload ./sample-alert.json", "underline")}
        """),
        formatter_class=argparse.RawTextHelpFormatter,  # Will be CustomHelpFormatter
    )
    setup_func_name_arg(alert_parser)

    alert_parser.add_argument(
        "--alertPayload",
        "-ap",
        type=str,
        required=True,
        help="path to alert payload JSON file",
        metavar="file/path.json",
    ).completer = comp.files(["json"])

    # scheduled run
    schedule_parser = run_subparsers.add_parser(
        "schedule",
        help="simulate a scheduled Function invocation",
        description=description(f"""
        {f("Simulate a scheduled invocation of a Samsara Function.")}

        This mode tests your function as if it were triggered by an automated schedule.
        The function receives an {f("event", "italic")} object containing a {f("SamsaraFunctionTriggerSource", "italic")}
        key set to {f('"schedule"', "italic")}, along with any parameters from {f("config.json", "bright_white")}.

        {f("Important:", "yellow")} This command executes the function {f("once immediately", "italic")} to simulate a single
        scheduled event. It {f("does not", "bold")} start any background process or cron job to run the
        function repeatedly on a schedule.

        {f("Required arguments:", "yellow")}
        - {f("func_name", "bold")}: The name of the function (must have been initialized).

        {f("Example:", "green")}
        {f("samsara-fn run schedule daily-report-generator", "underline")}
        """),
        formatter_class=argparse.RawTextHelpFormatter,  # Will be CustomHelpFormatter
    )
    setup_func_name_arg(schedule_parser)

    # api run
    api_parser = run_subparsers.add_parser(
        "api",
        help="execute the function with an API invocation",
        description=description(f"""
        {f("Simulate an API invocation of an initialized Samsara Function.")}

        This mode simulates an API call to your function. The {f("event", "italic")} object passed
        to your handler will include a {f("SamsaraFunctionTriggerSource", "italic")} key set to {f('"api"', "italic")}.
        You can optionally provide a JSON file to override the default parameters
        defined during {f("samsara-fn init", "underline")}.

        {f("Required arguments:", "yellow")}
        - {f("func_name", "bold")}: The name of the function (must have been initialized).

        {f("Optional arguments:", "green")}
        - {f("parametersOverride", "bold")}: Path to a JSON file. If provided, these key-value pairs will override the parameters stored in {f("config.json", "bright_white")} for this specific run. The override is a flat dictionary of strings.

        {f("Example:", "green")}
        {f("samsara-fn run api my-api-handler", "underline")}
        {f("samsara-fn run api my-api-handler --parametersOverride ./test-params.json", "underline")}
        """),
        formatter_class=argparse.RawTextHelpFormatter,  # Will be CustomHelpFormatter
    )
    setup_func_name_arg(api_parser)

    api_parser.add_argument(
        "--parametersOverride",
        "-po",
        type=str,
        help="path to parameters override JSON file",
        metavar="file/path.json",
    ).completer = comp.files(["json"])


def map_run_args(args: argparse.Namespace) -> RunArgs:
    """Map run arguments to RunArgs."""
    return RunArgs(
        run_command=args.run_command,
        func_name=args.func_name,
        parametersOverride=getattr(args, "parametersOverride", None),
        alertPayload=getattr(args, "alertPayload", None),
    )


def handle_run(args: RunArgs) -> int:
    """Handle function execution."""
    func_dir = get_function_dir(args.func_name)
    if not Path(func_dir).exists():
        logger.error(f"Function '{args.func_name}' not found")
        return 1

    temp_dir = get_temp_dir(args.func_name)
    cleanup_directory(temp_dir, remove_root=False)

    run_result = None
    try:
        if args.run_command == "manual":
            run_result = handle_manual_run(args, func_dir)
        elif args.run_command == "api":
            run_result = handle_api_run(args, func_dir)
        elif args.run_command == "alertAction":
            run_result = handle_alert_action_run(args, func_dir)
        elif args.run_command == "schedule":
            run_result = handle_schedule_run(func_dir)
    except Exception:
        logger.error(f"Runtime exception in Function {args.func_name}")
        raise

    if isinstance(run_result, int):
        return run_result

    if run_result is not None:
        # Print function result as JSON for piping
        try:
            print(json.dumps(run_result))
        except TypeError as e:
            logger.error(
                f"Function return value is not JSON serializable because {e}, printing as is"
            )
            print(run_result)

    return 0
