import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

from samsara_fn.helptext import description, f


@dataclass
class DependenciesArgs:
    """Arguments for dependencies command."""

    version: str
    is_install: bool


def setup_dependencies_parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up dependencies command parser."""
    dependencies_parser = subparsers.add_parser(
        "dependencies",
        help="install Python packages available in the Samsara Functions production runtime",
        description=description(f"""
        {f("Manage local Python dependencies to match the Samsara Functions production environment.")}

        By default, your locally executed functions can access any package available in your
        current Python environment. The {f("boto3", "italic")} AWS SDK is automatically made available.

        Samsara Functions also provide a curated set of additional Python packages in the production runtime.
        This command helps you install these specific package versions into your current
        local Python environment, ensuring consistency between local testing and production.

        {f("Important:", "yellow")} This command uses {f("pip install", "italic")} to install the selected
        dependency set directly into your active Python environment if {f("--install", "italic")} is specified. 
        Ensure your environment (e.g. a virtual environment) is set up as desired before running, or use the text output to
        create a requirements file for later use.

        {f("Example:", "green")}
        {f("samsara-fn dependencies latest > requirements.txt", "underline")}
        {f("samsara-fn dependencies latest --install", "underline")}
        """),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    dependencies_parser.add_argument(
        "version",
        choices=dependency_option_to_version.keys(),
        help="version of the dependencies file to print",
    )

    dependencies_parser.add_argument(
        "--install",
        "-i",
        action="store_true",
        help="install the dependencies into your active Python environment",
    )


def map_dependencies_args(args: argparse.Namespace) -> DependenciesArgs:
    """Map dependencies arguments to DependenciesArgs."""
    return DependenciesArgs(
        version=args.version,
        is_install=args.install,
    )


dependency_option_to_version = {
    "latest": "v8",
    "v8": "v8",
    "v7": "v7",
    "v6": "v6",
}


def handle_dependencies(args: DependenciesArgs) -> int:
    dependencies_path = (
        Path(__file__).parent
        / ".."
        / "artifacts"
        / "dependencies"
        / f"{dependency_option_to_version[args.version]}.txt"
    )

    if not args.is_install:
        with dependencies_path.open("r") as file:
            for line in file:
                print(line.strip())
        return 0

    res = subprocess.run(["pip", "install", "-r", str(dependencies_path)])
    return res.returncode
