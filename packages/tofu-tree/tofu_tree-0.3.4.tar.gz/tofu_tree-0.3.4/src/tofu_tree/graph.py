"""
Graph structure for Terraform/OpenTofu plan resources.

Builds a hierarchical tree/graph representation from resource addresses,
organizing them by module, resource type, and instance keys.
"""

from __future__ import annotations

import re
from typing import Any

# Action to symbol mapping
ACTION_SYMBOLS: dict[str, str] = {
    "created": "+",
    "destroyed": "-",
    "replaced": "±",
    "updated": "~",
}

# Symbol priority for aggregation (order matters: create > destroy > replace > update)
SYMBOL_PRIORITY: list[str] = ["+", "-", "±", "~"]


class ResourceGraph:
    """
    Represents a hierarchical graph structure of Terraform/OpenTofu resources.

    The graph organizes resources into a tree based on their addresses,
    supporting modules, resource types, and indexed instances.

    Example:
        >>> graph = ResourceGraph()
        >>> graph.add_resource({
        ...     'address': 'module.vpc.aws_subnet.public["a"]',
        ...     'action': 'created',
        ...     'symbol': '+'
        ... })
        >>> tree = graph.get_tree()
    """

    def __init__(self) -> None:
        """Initialize an empty resource graph."""
        self.tree: dict[str, Any] = {}
        self.resources: list[dict[str, str]] = []

    def add_resource(self, resource: dict[str, str]) -> None:
        """
        Add a resource to the graph.

        Args:
            resource: Dictionary with 'address', 'action', and 'symbol' keys.
        """
        self.resources.append(resource)
        self._add_to_tree(resource)

    def _add_to_tree(self, resource: dict[str, str]) -> None:
        """Add resource to the tree structure."""
        address_parts = self._normalize_address(resource["address"])
        current_node = self.tree

        for i, part in enumerate(address_parts):
            is_last_part = i == len(address_parts) - 1
            index_match = re.search(r"\[([^\]]+)\]", part)

            if index_match:
                current_node = self._handle_indexed_part(
                    current_node, part, index_match, resource, is_last_part
                )
            else:
                current_node = self._handle_simple_part(
                    current_node, part, resource, is_last_part
                )

    def _normalize_address(self, address: str) -> list[str]:
        """
        Normalize address by treating module.* as a single entity.

        Args:
            address: Resource address like 'module.vpc.aws_instance.web'

        Returns:
            List of address parts with module prefix combined.
        """
        parts = address.split(".")
        if len(parts) > 1 and parts[0] == "module":
            return [f"{parts[0]}.{parts[1]}", *parts[2:]]
        return parts

    def _handle_indexed_part(
        self,
        current_node: dict[str, Any],
        part: str,
        index_match: re.Match[str],
        resource: dict[str, str],
        is_last_part: bool,
    ) -> dict[str, Any]:
        """Handle a part with an index like resource_type["key"]."""
        base_name = part[: part.index("[")]
        index_value = index_match.group(1).strip("\"'")

        if base_name not in current_node:
            current_node[base_name] = []

        if is_last_part:
            current_node[base_name].append({"key": index_value, "resource": resource})
            return current_node

        # Find or create the indexed item
        indexed_item = self._find_or_create_indexed_item(
            current_node[base_name], index_value
        )
        children: dict[str, Any] = indexed_item["children"]
        return children

    def _find_or_create_indexed_item(
        self, indexed_list: list[dict[str, Any]], index_value: str
    ) -> dict[str, Any]:
        """Find existing indexed item or create a new one."""
        for item in indexed_list:
            if isinstance(item, dict) and item.get("key") == index_value:
                if "children" not in item:
                    item["children"] = {}
                return item

        new_item: dict[str, Any] = {"key": index_value, "children": {}}
        indexed_list.append(new_item)
        return new_item

    def _handle_simple_part(
        self,
        current_node: dict[str, Any],
        part: str,
        resource: dict[str, str],
        is_last_part: bool,
    ) -> dict[str, Any]:
        """Handle a simple part without an index."""
        if is_last_part:
            if "resources" not in current_node:
                current_node["resources"] = []
            current_node["resources"].append(resource)
            return current_node

        if part not in current_node or "children" not in current_node[part]:
            current_node[part] = {"children": {}}

        children: dict[str, Any] = current_node[part]["children"]
        return children

    def get_tree(self) -> dict[str, Any]:
        """Get the tree structure."""
        return self.tree

    def get_resources(self) -> list[dict[str, str]]:
        """Get all resources."""
        return self.resources

    @staticmethod
    def get_resource_symbols(node: dict[str, Any] | list[Any]) -> list[str]:
        """
        Extract all symbols from resources in this node.

        Args:
            node: A tree node (dict or list)

        Returns:
            List of symbol strings found in the node.
        """
        symbols: list[str] = []

        if isinstance(node, list):
            symbols.extend(ResourceGraph._extract_symbols_from_list(node))
        elif isinstance(node, dict):
            symbols.extend(ResourceGraph._extract_symbols_from_dict(node))

        return symbols

    @staticmethod
    def _extract_symbols_from_list(items: list[Any]) -> list[str]:
        """Extract symbols from a list of items."""
        symbols: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue

            if "resource" in item:
                symbols.append(item["resource"]["symbol"])
            elif "children" in item:
                symbols.extend(ResourceGraph.get_resource_symbols(item["children"]))

        return symbols

    @staticmethod
    def _extract_symbols_from_dict(node: dict[str, Any]) -> list[str]:
        """Extract symbols from a dict node."""
        symbols: list[str] = []

        for value in node.values():
            if isinstance(value, list):
                symbols.extend(ResourceGraph._extract_symbols_from_list(value))
            elif isinstance(value, dict):
                if "resources" in value:
                    symbols.extend(r["symbol"] for r in value["resources"])
                if "children" in value:
                    symbols.extend(
                        ResourceGraph.get_resource_symbols(value["children"])
                    )
                else:
                    symbols.extend(ResourceGraph.get_resource_symbols(value))

        return symbols

    @staticmethod
    def get_aggregate_symbol(symbols: list[str]) -> str:
        """
        Get a single symbol representing all symbols.

        Priority order: + (created) > - (destroyed) > ~ (replaced/updated)

        Args:
            symbols: List of symbol strings

        Returns:
            Single aggregate symbol or empty string if no symbols.
        """
        if not symbols:
            return ""

        for symbol in SYMBOL_PRIORITY:
            if symbol in symbols:
                return symbol

        return "?"


def parse_plan_output(lines: list[str]) -> list[dict[str, str]]:
    """
    Parse terraform/tofu plan concise output and extract resource changes.

    Args:
        lines: List of lines from plan output

    Returns:
        List of resource dictionaries with 'address', 'action', and 'symbol' keys.

    Example:
        >>> lines = ["# aws_instance.web will be created"]
        >>> resources = parse_plan_output(lines)
        >>> resources[0]['action']
        'created'
    """
    resources: list[dict[str, str]] = []
    in_plan_section = False

    resource_pattern = re.compile(
        r"^\s*#\s+(.+?)\s+(?:will be|must be)\s+(created|destroyed|replaced|updated)"
    )

    for line in lines:
        line = line.strip()

        if "will perform the following actions" in line.lower():
            in_plan_section = True
            continue

        if not in_plan_section:
            continue

        match = resource_pattern.match(line)
        if match:
            address = match.group(1)
            action = match.group(2)
            symbol = ACTION_SYMBOLS.get(action, "?")

            resources.append({"address": address, "action": action, "symbol": symbol})

    return resources


def build_graph(resources: list[dict[str, str]]) -> ResourceGraph:
    """
    Build a ResourceGraph from a list of resources.

    Args:
        resources: List of resource dictionaries

    Returns:
        ResourceGraph instance with all resources added.
    """
    graph = ResourceGraph()
    for resource in resources:
        graph.add_resource(resource)
    return graph
