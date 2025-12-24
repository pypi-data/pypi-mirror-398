"""
tofu-tree: A beautiful tree visualization tool for Terraform/OpenTofu plan output.

Transform your `terraform plan` or `tofu plan` output into an easy-to-read
hierarchical tree structure with color-coded symbols.
"""

from tofu_tree.cli import main
from tofu_tree.graph import (
    ACTION_SYMBOLS,
    SYMBOL_PRIORITY,
    ResourceGraph,
    build_graph,
    parse_plan_output,
)
from tofu_tree.printer import TreePrinter, color_symbol

__version__ = "0.2.1"
__author__ = "Mohamed Amin"
__email__ = "your.email@example.com"

__all__ = [
    "ACTION_SYMBOLS",
    "SYMBOL_PRIORITY",
    "ResourceGraph",
    "TreePrinter",
    "__version__",
    "build_graph",
    "color_symbol",
    "main",
    "parse_plan_output",
]
