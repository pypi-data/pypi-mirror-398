"""
Tree printer module for Terraform/OpenTofu plan tree output.

Uses position-based prefix logic similar to the Unix 'tree' command
to display hierarchical resource structures.
"""

from __future__ import annotations

import re
from typing import Any

from tofu_tree.graph import ResourceGraph

# ANSI color codes
COLOR_GREEN = "\033[32m"
COLOR_RED = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_RESET = "\033[0m"

# Position types
ONLY = "only"
FIRST = "first"
MIDDLE = "middle"
LAST = "last"

# Connectors per position
CONNECTORS: dict[str, str] = {
    ONLY: "└── ",
    FIRST: "├── ",
    MIDDLE: "├── ",
    LAST: "└── ",
}

# Inherited prefix per position (for children)
INHERITED: dict[str, str] = {
    ONLY: "    ",
    FIRST: "│   ",
    MIDDLE: "│   ",
    LAST: "    ",
}


def color_symbol(symbol: str, use_color: bool = False) -> str:
    """
    Color the symbol based on its value.

    Args:
        symbol: The symbol to color (+/-/~)
        use_color: Whether to apply ANSI colors

    Returns:
        Colored symbol string if use_color is True, otherwise plain symbol.
    """
    if not use_color:
        return symbol

    color_map = {
        "+": COLOR_GREEN,
        "-": COLOR_RED,
        "~": COLOR_YELLOW,
    }

    color_code = color_map.get(symbol, "")
    return f"{color_code}{symbol}{COLOR_RESET}" if color_code else symbol


class TreePrinter:
    """
    Prints tree structures with position-based prefixes.

    Creates beautiful tree output similar to the Unix 'tree' command,
    with proper connectors (├──, └──) and vertical lines (│).

    Example:
        >>> printer = TreePrinter(use_color=True)
        >>> printer.print_tree(graph.get_tree())
        >>> printer.print_summary(graph.get_resources())
    """

    def __init__(self, use_color: bool = False) -> None:
        """
        Initialize the tree printer.

        Args:
            use_color: Whether to use ANSI colors for symbols.
        """
        self.use_color = use_color

    def print_tree(self, node: dict[str, Any], inherited_prefix: str = "") -> None:
        """
        Print the tree structure using position-based prefixes.

        Args:
            node: The tree node (dict) to print
            inherited_prefix: Accumulated prefix from all ancestors
        """
        if not isinstance(node, dict):
            return

        keys = self._get_sorted_keys(node)
        is_root_level = inherited_prefix == ""

        for i, key in enumerate(keys):
            value = node[key]

            # Determine position
            if len(keys) == 1:
                position = ONLY
            elif i == 0:
                position = FIRST
            elif i == len(keys) - 1:
                position = LAST
            else:
                position = MIDDLE

            # Build current line prefix
            connector = CONNECTORS[position]
            current_prefix = inherited_prefix + connector

            # Build inherited prefix for children
            if is_root_level:
                next_inherited = INHERITED[FIRST]
            else:
                next_inherited = inherited_prefix + INHERITED[position]

            # Print node header
            if isinstance(value, list):
                self._print_list_node(
                    value, key, current_prefix, next_inherited, is_root_level
                )
            elif isinstance(value, dict):
                self._print_dict_node(
                    value, key, current_prefix, next_inherited, is_root_level
                )

    def _get_sorted_keys(self, node: dict[str, Any]) -> list[str]:
        """Get sorted keys excluding internal keys."""
        return sorted([k for k in node if k not in ["children", "resources"]])

    def _format_symbol(self, symbol: str) -> str:
        """Format symbol with color if enabled."""
        if not symbol:
            return ""
        colored = color_symbol(symbol, self.use_color)
        return f"{colored} "

    def _print_list_node(
        self,
        value: list[Any],
        key: str,
        current_prefix: str,
        next_inherited: str,
        is_root_level: bool,
    ) -> None:
        """Print a node that contains a list of indexed items."""
        all_symbols = self._collect_symbols_from_list(value)
        symbol_str = self._format_symbol(
            ResourceGraph.get_aggregate_symbol(all_symbols)
        )

        if is_root_level:
            print(f"{symbol_str}{key}")
            if next_inherited == INHERITED[FIRST]:
                next_inherited = "│  "
        else:
            print(f"{current_prefix}{symbol_str}{key}")

        sorted_items = sorted(value, key=lambda x: x.get("key", ""))
        for j, item in enumerate(sorted_items):
            item_position = self._get_position(j, len(sorted_items))
            item_connector = CONNECTORS[item_position]
            item_prefix = next_inherited + item_connector
            item_next_inherited = next_inherited + INHERITED[item_position]

            self._print_list_item(item, item_prefix, item_next_inherited)
            if item_position in (LAST, ONLY):
                print(item_next_inherited)

    def _print_dict_node(
        self,
        value: dict[str, Any],
        key: str,
        current_prefix: str,
        next_inherited: str,
        is_root_level: bool,
    ) -> None:
        """Print a dict node, handling different dict structures."""
        if "children" in value:
            self._print_dict_with_children(
                value, key, current_prefix, next_inherited, is_root_level
            )
        elif "resources" in value:
            self._print_dict_with_resources(
                value, key, current_prefix, next_inherited, is_root_level
            )
        else:
            self._print_dict_node_only(
                value, key, current_prefix, next_inherited, is_root_level
            )

    def _print_dict_with_children(
        self,
        value: dict[str, Any],
        key: str,
        current_prefix: str,
        next_inherited: str,
        is_root_level: bool,
    ) -> None:
        """Print a dict node that has children."""
        children = value["children"]
        child_keys = sorted([k for k in children if k != "resources"])
        has_resources = "resources" in children

        all_symbols = self._collect_symbols_from_dict_with_children(
            children, child_keys
        )
        symbol_str = self._format_symbol(
            ResourceGraph.get_aggregate_symbol(all_symbols)
        )

        if is_root_level:
            print(f"{symbol_str}{key}")
            next_inherited = "│  "
        else:
            print(f"{current_prefix}{symbol_str}{key}")

        if has_resources:
            resources = children["resources"]
            sorted_resources = sorted(
                resources, key=lambda r: self._extract_resource_name(r["address"])
            )

            has_children_after = len(child_keys) > 0

            for k, resource in enumerate(sorted_resources):
                if has_children_after:
                    res_position = FIRST if k == 0 else MIDDLE
                else:
                    res_position = self._get_position(k, len(sorted_resources))

                res_connector = CONNECTORS[res_position]
                res_prefix = next_inherited + res_connector
                res_next_inherited = next_inherited + INHERITED[res_position]

                name = self._extract_resource_name(resource["address"])
                colored_symbol = color_symbol(resource["symbol"], self.use_color)
                print(f"{res_prefix}{colored_symbol} {name}")

                if res_position in (LAST, ONLY):
                    print(res_next_inherited)

        for j, child_key in enumerate(child_keys):
            child_position = self._get_position(j, len(child_keys))
            child_connector = CONNECTORS[child_position]
            child_prefix = next_inherited + child_connector
            child_next_inherited = next_inherited + INHERITED[child_position]

            child_value = children[child_key]
            if isinstance(child_value, dict) and "children" in child_value:
                child_symbols = ResourceGraph.get_resource_symbols(child_value)
                child_symbol_str = self._format_symbol(
                    ResourceGraph.get_aggregate_symbol(child_symbols)
                )
                print(f"{child_prefix}{child_symbol_str}{child_key}")
                self.print_tree(child_value["children"], child_next_inherited)
            elif isinstance(child_value, list):
                all_symbols = self._collect_symbols_from_list(child_value)
                symbol_str = self._format_symbol(
                    ResourceGraph.get_aggregate_symbol(all_symbols)
                )
                print(f"{child_prefix}{symbol_str}{child_key}")
                sorted_items = sorted(child_value, key=lambda x: x.get("key", ""))
                for k, item in enumerate(sorted_items):
                    item_position = self._get_position(k, len(sorted_items))
                    item_connector = CONNECTORS[item_position]
                    item_prefix = child_next_inherited + item_connector
                    item_next_inherited = (
                        child_next_inherited + INHERITED[item_position]
                    )

                    self._print_list_item(item, item_prefix, item_next_inherited)
                    if item_position in (LAST, ONLY):
                        print(item_next_inherited)
            else:
                self.print_tree({child_key: child_value}, child_next_inherited)

    def _print_dict_with_resources(
        self,
        value: dict[str, Any],
        key: str,
        current_prefix: str,
        next_inherited: str,
        is_root_level: bool,
    ) -> None:
        """Print a dict node that has resources."""
        all_symbols = [r["symbol"] for r in value["resources"]]
        symbol_str = self._format_symbol(
            ResourceGraph.get_aggregate_symbol(all_symbols)
        )

        if is_root_level:
            print(f"{symbol_str}{key}")
        else:
            print(f"{current_prefix}{symbol_str}{key}")

        resources = value["resources"]
        sorted_resources = sorted(
            resources, key=lambda r: self._extract_resource_name(r["address"])
        )

        for k, resource in enumerate(sorted_resources):
            res_position = self._get_position(k, len(sorted_resources))
            res_connector = CONNECTORS[res_position]
            res_prefix = next_inherited + res_connector
            res_next_inherited = next_inherited + INHERITED[res_position]

            name = self._extract_resource_name(resource["address"])
            colored_symbol = color_symbol(resource["symbol"], self.use_color)
            print(f"{res_prefix}{colored_symbol} {name}")

            if res_position in (LAST, ONLY):
                print(res_next_inherited)

    def _print_dict_node_only(
        self,
        value: dict[str, Any],
        key: str,
        current_prefix: str,
        next_inherited: str,
        is_root_level: bool,
    ) -> None:
        """Print a dict node without explicit children or resources."""
        all_symbols = ResourceGraph.get_resource_symbols(value)
        symbol_str = self._format_symbol(
            ResourceGraph.get_aggregate_symbol(all_symbols)
        )

        if is_root_level:
            print(f"{symbol_str}{key}")
        else:
            print(f"{current_prefix}{symbol_str}{key}")

        self.print_tree(value, next_inherited)

    def _print_list_item(
        self,
        item: dict[str, Any],
        item_prefix: str,
        item_next_inherited: str,
    ) -> None:
        """Print a single item from a list node."""
        if "resource" in item:
            resource = item["resource"]
            resource_name = self._extract_resource_name(resource["address"])
            colored_symbol = color_symbol(resource["symbol"], self.use_color)
            print(f"{item_prefix}{colored_symbol} {resource_name}: {item['key']}")
        elif "children" in item:
            print(f"{item_prefix}{item['key']}")
            self.print_tree(item["children"], item_next_inherited)

    def _get_position(self, index: int, total: int) -> str:
        """
        Determine position based on index and total count.

        Args:
            index: Current index (0-based)
            total: Total number of items

        Returns:
            Position string (ONLY, FIRST, MIDDLE, or LAST)
        """
        if total == 1:
            return ONLY
        elif index == 0:
            return FIRST
        elif index == total - 1:
            return LAST
        else:
            return MIDDLE

    def _extract_resource_name(self, address: str) -> str:
        """Extract resource name from address, removing index brackets."""
        return re.sub(r"\[.*\]", "", address.split(".")[-1])

    def _collect_symbols_from_list(self, items: list[Any]) -> list[str]:
        """Collect all symbols from a list of items."""
        symbols: list[str] = []
        for item in items:
            if "resource" in item:
                symbols.append(item["resource"]["symbol"])
            elif "children" in item:
                symbols.extend(ResourceGraph.get_resource_symbols(item["children"]))
        return symbols

    def _collect_symbols_from_dict_with_children(
        self, children: dict[str, Any], child_keys: list[str]
    ) -> list[str]:
        """Collect symbols from a dict with children."""
        all_symbols: list[str] = []

        if "resources" in children:
            all_symbols.extend([r["symbol"] for r in children["resources"]])

        for child_key in child_keys:
            all_symbols.extend(ResourceGraph.get_resource_symbols(children[child_key]))

        return all_symbols

    def print_summary(self, resources: list[dict[str, str]]) -> None:
        """
        Print summary of resource changes.

        Args:
            resources: List of resource dictionaries
        """
        SUMMARY_WIDTH = 3
        counts = self._count_resources_by_symbol(resources)

        created_symbol = color_symbol("+", self.use_color)
        destroyed_symbol = color_symbol("-", self.use_color)
        modified_symbol = color_symbol("~", self.use_color)

        print(
            f"{created_symbol} {counts['+']:{SUMMARY_WIDTH}d} resources to be created"
        )
        print(
            f"{destroyed_symbol} {counts['-']:{SUMMARY_WIDTH}d} resources to be destroyed"
        )
        print(
            f"{modified_symbol} {counts['~']:{SUMMARY_WIDTH}d} resources to be replaced/updated"
        )

    def _count_resources_by_symbol(
        self, resources: list[dict[str, str]]
    ) -> dict[str, int]:
        """Count resources grouped by their symbol."""
        counts: dict[str, int] = {"+": 0, "-": 0, "~": 0}

        for resource in resources:
            symbol = resource.get("symbol", "?")
            if symbol in counts:
                counts[symbol] += 1

        return counts
