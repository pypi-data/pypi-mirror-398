# PYTHON_ARGCOMPLETE_OK

import os
import sys
import argparse

from samsara_fn.helptext import description, f
from samsara_fn.clilogger import update_verbosity
from samsara_fn.commands.init import (
    handle_init,
    setup_init_parser,
    map_init_args,
)
from samsara_fn.commands.run import (
    handle_run,
    setup_run_parser,
    map_run_args,
)
from samsara_fn.commands.schemas import (
    handle_schemas,
    setup_schemas_parser,
    map_schemas_args,
)
from samsara_fn.commands.dependencies import (
    handle_dependencies,
    setup_dependencies_parser,
    map_dependencies_args,
)
from samsara_fn.commands.templates import (
    handle_templates,
    setup_templates_parser,
    map_templates_args,
)
from samsara_fn.commands.bundle import (
    handle_bundle,
    setup_bundle_parser,
    map_bundle_args,
)
from samsara_fn.commands.completion import completion


class CustomArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser to ensure consistent formatting across platforms."""

    def error(self, message):
        """Override error method to ensure consistent choice formatting."""
        # Add quotes to choices in error messages to match Linux format
        if "invalid choice:" in message and "(choose from" in message:
            parts = message.split("(choose from", 1)
            choices_part = parts[1].strip()

            # Add quotes to choices if they don't already have them
            if not all(choice.startswith("'") for choice in choices_part.split(", ")):
                choices = [
                    f"'{choice}'" for choice in choices_part.rstrip(")").split(", ")
                ]
                message = f"{parts[0]}(choose from {', '.join(choices)})"

        # Use standard error handling
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\n")


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the main argument parser."""
    parser = CustomArgumentParser(
        description=description(f"""
        {f("Samsara Functions Simulator CLI")}
        
        Your local development companion for {f("Samsara Functions", "italic")}.
        This tool mirrors the production environment to simplify your development workflow, allowing you to:
        
        - Initialize and configure new functions locally, mirroring the Samsara dashboard setup (see {f("samsara-fn init --help", "underline")}).
        - Execute your functions in various simulated scenarios (see {f("samsara-fn run --help", "underline")}).
        - Manage and align local Python dependencies with the production runtime (see {f("samsara-fn dependencies --help", "underline")}).
        - Print JSON schemas to aid in the development of function configurations (see {f("samsara-fn schemas --help", "underline")}).
        - Generate code templates for common function patterns (see {f("samsara-fn templates --help", "underline")}).
        - Bundle source code into deployment-ready zip files (see {f("samsara-fn bundle --help", "underline")}).
        
        All necessary data is stored in the {f(".samsara-functions", "bright_white")} directory,
        automatically created by {f("samsara-fn init", "underline")} in your current working directory.
        
        AWS interactions (secrets, storage) are locally stubbed. Warnings are issued for unexpected AWS SDK calls.
        Inspect stubbed storage contents in {f(".samsara-functions/storage", "bright_white")}.
        """),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="enable verbose logging"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_init_parser(subparsers)
    setup_run_parser(subparsers)
    setup_schemas_parser(subparsers)
    setup_dependencies_parser(subparsers)
    setup_templates_parser(subparsers)
    setup_bundle_parser(subparsers)

    completion().init(parser)
    return parser


def main() -> int:
    """Main entry point for the CLI."""
    args = create_parser().parse_args()

    if args.verbose:
        os.environ["SAMSARA_SIMULATOR_VERBOSE"] = "1"
        update_verbosity()

    if args.command == "init":
        return handle_init(map_init_args(args))

    if args.command == "run":
        return handle_run(map_run_args(args))

    if args.command == "schemas":
        return handle_schemas(map_schemas_args(args))

    if args.command == "dependencies":
        return handle_dependencies(map_dependencies_args(args))

    if args.command == "templates":
        return handle_templates(map_templates_args(args))

    if args.command == "bundle":
        return handle_bundle(map_bundle_args(args))


if __name__ == "__main__":
    sys.exit(main())
