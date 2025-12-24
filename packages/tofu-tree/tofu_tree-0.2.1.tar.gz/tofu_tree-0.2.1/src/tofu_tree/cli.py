"""
Command-line interface for tofu-tree.

Provides the main entry point for the tofu-tree command,
handling argument parsing and orchestrating the plan parsing and display.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from tofu_tree.graph import build_graph, parse_plan_output
from tofu_tree.printer import TreePrinter


def find_terraform_command() -> str | None:
    """
    Find available terraform command (terraform or tofu).

    Returns:
        Command name ('tofu' or 'terraform') or None if neither is found.
    """
    if shutil.which("tofu"):
        return "tofu"
    elif shutil.which("terraform"):
        return "terraform"
    else:
        return None


def run_plan_command(path: str | None = None) -> list[str]:
    """
    Run terraform/tofu plan command and return output lines.

    Args:
        path: Directory path to run the plan in. Defaults to current directory.

    Returns:
        List of output lines from the plan command.

    Raises:
        SystemExit: If no terraform/tofu command is found or path is invalid.
    """
    cmd = find_terraform_command()
    if not cmd:
        print(
            "Error: Neither 'terraform' nor 'tofu' command found in PATH.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Default to current directory if no path provided
    if path is None:
        resolved_path = Path.cwd()
    else:
        resolved_path = Path(path).resolve()
        if not resolved_path.is_dir():
            print(f"Error: Path '{path}' is not a valid directory.", file=sys.stderr)
            sys.exit(1)

    try:
        result = subprocess.run(
            [cmd, "plan", "-concise", "-no-color"],
            capture_output=True,
            text=True,
            check=False,
            cwd=resolved_path,
        )
        # Combine stdout and stderr (terraform/tofu may output to stderr)
        output = result.stdout + result.stderr
        return output.splitlines(keepends=True)
    except Exception as e:
        print(f"Error running {cmd} plan: {e}", file=sys.stderr)
        sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="tofu-tree",
        description="Parse Terraform/OpenTofu plan output and display as a beautiful tree",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tofu-tree                     Run plan in current directory
  tofu-tree /path/to/tf         Run plan in specified directory
  tofu plan -concise | tofu-tree --input
                                Read plan output from stdin
  tofu-tree --no-color          Disable colored output

For more information, visit: https://github.com/yourusername/tofu-tree
        """,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s 0.2.1",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output for symbols (color is enabled by default)",
    )
    parser.add_argument(
        "--input",
        "-i",
        action="store_true",
        help="Read plan output from stdin instead of running terraform/tofu plan",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Path to the Terraform/OpenTofu directory (default: current directory)",
    )
    return parser


def main() -> None:
    """
    Main entry point for the tofu-tree command.

    Parses arguments, runs the plan (or reads from stdin),
    and displays the tree visualization.
    """
    parser = create_parser()
    args = parser.parse_args()

    # Get input lines
    lines = sys.stdin.readlines() if args.input else run_plan_command(args.path)

    # Parse input
    resources = parse_plan_output(lines)

    if not resources:
        print("No resource changes found in plan output.", file=sys.stderr)
        sys.exit(1)

    # Build graph structure
    graph = build_graph(resources)

    # Print tree and summary (color enabled by default)
    printer = TreePrinter(use_color=not args.no_color)
    printer.print_tree(graph.get_tree())
    print()  # Empty line before summary
    printer.print_summary(graph.get_resources())

    return None


if __name__ == "__main__":
    main()
