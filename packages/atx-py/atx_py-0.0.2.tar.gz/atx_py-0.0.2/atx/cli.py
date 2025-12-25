import argparse
import re
import subprocess
import sys
from pathlib import Path


def tool_output_filepath(
    output_dir: Path, tool_name: str, tool_version: str, output_filename: str
) -> Path:
    return (
        output_dir.joinpath(tool_name).joinpath(tool_version).joinpath(output_filename)
    )


def build_command(
    script_filepath: Path,
    *,
    output_dir: Path,
    tool_name: str,
    tool_version: str,
    output_filename: str,
) -> Path:
    """
    Build a standalone executable from a Python script using Nuitka.
    Returns the path to the generated executable.
    """
    if not script_filepath.is_file():
        raise FileNotFoundError(f"Script file not found: {script_filepath}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_filename = output_filename.strip()
    tool_name = tool_name.strip()
    tool_version = tool_version.strip()
    tool_version = tool_version.replace(".", "_").strip()
    if (
        not re.match(r"^[a-zA-Z0-9_]+$", output_filename)
        or len(output_filename) > 127
        or len(output_filename) < 3
    ):
        raise ValueError(
            "Argument '--output-filename' must be 3-127 characters long and "
            + "contain only letters, numbers, underscores, and hyphens"
        )
    if (
        not re.match(r"^[a-zA-Z0-9_]+$", tool_name)
        or len(tool_name) > 127
        or len(tool_name) < 3
    ):
        raise ValueError(
            "Argument '--tool-name' must be 3-127 characters long and "
            + "contain only letters, numbers, underscores, and hyphens"
        )
    if (
        not re.match(r"^[a-zA-Z0-9_]+$", tool_version)
        or len(tool_version) > 63
        or len(tool_version) < 1
    ):
        raise ValueError(
            "Argument '--tool-version' must be 1-63 characters long and "
            + "contain only letters, numbers, underscores, and hyphens"
        )

    output_filepath = tool_output_filepath(
        output_dir=output_dir,
        tool_name=tool_name,
        tool_version=tool_version,
        output_filename=output_filename,
    )

    command: list[str] = [
        "hot-tool",
        "build",
        f"-o={output_filepath}",
        str(script_filepath),
    ]

    subprocess.check_call(command)

    return output_filepath


def handle_build_command(args: argparse.Namespace) -> None:
    """Handle the build subcommand."""
    script_filepath = Path(args.script)
    output_dir = Path(args.output_dir)
    tool_name: str = args.tool_name.strip()
    tool_version: str = args.tool_version.strip()
    output_filename: str = args.output_filename.strip()

    try:
        result_path = build_command(
            script_filepath,
            tool_name=tool_name,
            tool_version=tool_version,
            output_dir=output_dir,
            output_filename=output_filename,
        )
        print(f"Standalone script saved to '{result_path.resolve()}'")
        sys.exit(0)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)


def main() -> None:
    """CLI entry point for atx."""
    parser = argparse.ArgumentParser(
        prog="atx",
        description="Build standalone executables from Python scripts",
        epilog="For more information, visit: https://bitbucket.org/aiello_sharif/atx/",  # noqa: E501
    )

    # Create subparsers
    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
        help="Use 'atx <command> --help' for more information",
        required=True,
    )

    # Build subcommand
    build_parser = subparsers.add_parser(
        "build",
        help="Build a standalone executable from a Python script",
        description="Compile a Python script into a standalone executable using Nuitka",
    )
    build_parser.add_argument(
        "script",
        type=str,
        help="Path to the input Python script file",
    )
    build_parser.add_argument(
        "--tool-name",
        type=str,
        required=True,
        help="Name of the tool",
    )
    build_parser.add_argument(
        "--tool-version",
        type=str,
        required=True,
        help="Version of the tool",
    )
    build_parser.add_argument(
        "--output-dir",
        type=str,
        default="./dist/",
        help="Output directory for the tool (default: current directory)",
    )
    build_parser.add_argument(
        "--output-filename",
        type=str,
        default="tool",
        help="Output filename for the tool (default: tool)",
    )
    build_parser.set_defaults(func=handle_build_command)

    # Parse arguments
    args = parser.parse_args()

    # Dispatch to the appropriate handler
    args.func(args)
