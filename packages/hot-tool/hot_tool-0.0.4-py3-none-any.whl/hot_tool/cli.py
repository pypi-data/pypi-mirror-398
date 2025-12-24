"""
CLI interface for hot-tool.

Usage:
    hot-tool build script.py [-o OUTPUT]
"""

import argparse
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from textwrap import dedent


def make_script_runnable(script: str) -> str:
    """
    Transform a script into a runnable tool executable.
    Appends the necessary code to call run_as_executable().
    """
    return (
        script.strip()
        + "\n\n\n"
        + dedent(
            """
            from hot_tool.run import run_as_executable

            run_as_executable()
            """
        ).strip()
    )


def build_command(script_filepath: Path, output_filepath: Path | None = None) -> Path:
    """
    Build a standalone executable from a Python script using Nuitka.
    Returns the path to the generated executable.
    """
    if not script_filepath.is_file():
        raise FileNotFoundError(f"Script file not found: {script_filepath}")

    if output_filepath is None:
        output_filepath = script_filepath.parent.joinpath(script_filepath.stem)
    output_filepath.parent.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile() as temp_file:
        temp_file.write(
            make_script_runnable(script_filepath.read_text()).encode("utf-8")
        )
        temp_file.flush()
        temp_file.seek(0)

        command: list[str] = [
            sys.executable,
            "-m",
            "nuitka",
            "--standalone",
            "--onefile",
            "--onefile-tempdir-spec={CACHE_DIR}/nuitka_onefile_tempdir_spec/"
            + output_filepath.stem,
            "--output-dir=.",
            "--remove-output",
            "-o",
            str(output_filepath),
            temp_file.name,
        ]

        try:
            print("Starting Nuitka compilation...")
            subprocess.check_call(command)
            print("Compilation completed successfully.")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Compilation failed with return code {e.returncode}"
            ) from e
        except FileNotFoundError as e:
            raise RuntimeError("Error: Nuitka or Python interpreter not found.") from e

    return output_filepath


def handle_build_command(args: argparse.Namespace) -> None:
    """Handle the build subcommand."""
    script_filepath = Path(args.script)
    output_filepath = Path(args.output) if args.output else None

    try:
        result_path = build_command(script_filepath, output_filepath)
        print(f"Standalone script saved to '{result_path.resolve()}'")
        sys.exit(0)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)


def main() -> None:
    """CLI entry point for hot-tool."""
    parser = argparse.ArgumentParser(
        prog="hot-tool",
        description="Build standalone executables from Python scripts",
        epilog="For more information, visit: https://github.com/allen2c/hot-tool",
    )

    # Create subparsers
    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
        help="Use 'hot-tool <command> --help' for more information",
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
        "-o",
        "--output",
        type=str,
        help="Path to the output executable (default: script name without extension)",
    )
    build_parser.set_defaults(func=handle_build_command)

    # Parse arguments
    args = parser.parse_args()

    # Dispatch to the appropriate handler
    args.func(args)
