"""Tests for the printer module."""

from __future__ import annotations

import io
from contextlib import redirect_stdout

from tofu_tree.graph import build_graph
from tofu_tree.printer import (
    COLOR_GREEN,
    COLOR_RED,
    COLOR_RESET,
    COLOR_YELLOW,
    TreePrinter,
    color_symbol,
)


class TestColorSymbol:
    """Tests for color_symbol function."""

    def test_color_disabled(self) -> None:
        """Test that color is not applied when disabled."""
        assert color_symbol("+", use_color=False) == "+"
        assert color_symbol("-", use_color=False) == "-"
        assert color_symbol("~", use_color=False) == "~"

    def test_color_enabled_plus(self) -> None:
        """Test green color for + symbol."""
        result = color_symbol("+", use_color=True)
        assert COLOR_GREEN in result
        assert COLOR_RESET in result
        assert "+" in result

    def test_color_enabled_minus(self) -> None:
        """Test red color for - symbol."""
        result = color_symbol("-", use_color=True)
        assert COLOR_RED in result
        assert COLOR_RESET in result
        assert "-" in result

    def test_color_enabled_tilde(self) -> None:
        """Test yellow color for ~ symbol."""
        result = color_symbol("~", use_color=True)
        assert COLOR_YELLOW in result
        assert COLOR_RESET in result
        assert "~" in result

    def test_color_unknown_symbol(self) -> None:
        """Test unknown symbol returns as-is."""
        assert color_symbol("?", use_color=True) == "?"
        assert color_symbol("x", use_color=True) == "x"


class TestTreePrinter:
    """Tests for TreePrinter class."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        printer = TreePrinter()
        assert printer.use_color is False

    def test_init_with_color(self) -> None:
        """Test initialization with color enabled."""
        printer = TreePrinter(use_color=True)
        assert printer.use_color is True

    def test_print_empty_tree(self) -> None:
        """Test printing empty tree produces no output."""
        printer = TreePrinter()
        output = io.StringIO()

        with redirect_stdout(output):
            printer.print_tree({})

        assert output.getvalue() == ""

    def test_print_simple_tree(self) -> None:
        """Test printing a simple tree."""
        resources = [
            {"address": "aws_instance.web", "action": "created", "symbol": "+"},
        ]
        graph = build_graph(resources)
        printer = TreePrinter(use_color=False)

        output = io.StringIO()
        with redirect_stdout(output):
            printer.print_tree(graph.get_tree())

        result = output.getvalue()
        assert "aws_instance" in result
        assert "+" in result

    def test_print_tree_with_color(self) -> None:
        """Test printing tree with color enabled."""
        resources = [
            {"address": "aws_instance.web", "action": "created", "symbol": "+"},
        ]
        graph = build_graph(resources)
        printer = TreePrinter(use_color=True)

        output = io.StringIO()
        with redirect_stdout(output):
            printer.print_tree(graph.get_tree())

        result = output.getvalue()
        assert COLOR_GREEN in result
        assert COLOR_RESET in result

    def test_print_tree_with_modules(self) -> None:
        """Test printing tree with module resources."""
        resources = [
            {
                "address": "module.vpc.aws_subnet.main",
                "action": "created",
                "symbol": "+",
            },
        ]
        graph = build_graph(resources)
        printer = TreePrinter(use_color=False)

        output = io.StringIO()
        with redirect_stdout(output):
            printer.print_tree(graph.get_tree())

        result = output.getvalue()
        assert "module.vpc" in result
        assert "aws_subnet" in result

    def test_print_tree_connectors(self) -> None:
        """Test that tree connectors are present."""
        resources = [
            {"address": "aws_instance.a", "action": "created", "symbol": "+"},
            {"address": "aws_instance.b", "action": "created", "symbol": "+"},
        ]
        graph = build_graph(resources)
        printer = TreePrinter(use_color=False)

        output = io.StringIO()
        with redirect_stdout(output):
            printer.print_tree(graph.get_tree())

        result = output.getvalue()
        # Should have tree connectors
        assert "├" in result or "└" in result


class TestTreePrinterSummary:
    """Tests for TreePrinter.print_summary method."""

    def test_print_summary_empty(self) -> None:
        """Test printing summary with no resources."""
        printer = TreePrinter(use_color=False)

        output = io.StringIO()
        with redirect_stdout(output):
            printer.print_summary([])

        result = output.getvalue()
        assert "0 resources to be created" in result
        assert "0 resources to be destroyed" in result
        assert "0 resources to be replaced/updated" in result

    def test_print_summary_counts(self) -> None:
        """Test summary counts resources correctly."""
        resources = [
            {"address": "a.1", "action": "created", "symbol": "+"},
            {"address": "a.2", "action": "created", "symbol": "+"},
            {"address": "b.1", "action": "destroyed", "symbol": "-"},
            {"address": "c.1", "action": "updated", "symbol": "~"},
            {"address": "c.2", "action": "replaced", "symbol": "~"},
        ]
        printer = TreePrinter(use_color=False)

        output = io.StringIO()
        with redirect_stdout(output):
            printer.print_summary(resources)

        result = output.getvalue()
        assert "2 resources to be created" in result
        assert "1 resources to be destroyed" in result
        assert "2 resources to be replaced/updated" in result

    def test_print_summary_with_color(self) -> None:
        """Test summary with color enabled."""
        resources = [
            {"address": "a.1", "action": "created", "symbol": "+"},
        ]
        printer = TreePrinter(use_color=True)

        output = io.StringIO()
        with redirect_stdout(output):
            printer.print_summary(resources)

        result = output.getvalue()
        assert COLOR_GREEN in result


class TestTreePrinterHelpers:
    """Tests for TreePrinter helper methods."""

    def test_extract_resource_name(self) -> None:
        """Test extracting resource name from address."""
        printer = TreePrinter()

        assert printer._extract_resource_name("aws_instance.web") == "web"
        assert printer._extract_resource_name('aws_instance.web["prod"]') == "web"
        assert printer._extract_resource_name("module.vpc.aws_subnet.main") == "main"

    def test_get_position(self) -> None:
        """Test position determination."""
        printer = TreePrinter()

        # Single item
        assert printer._get_position(0, 1) == "only"

        # First of many
        assert printer._get_position(0, 3) == "first"

        # Middle
        assert printer._get_position(1, 3) == "middle"

        # Last
        assert printer._get_position(2, 3) == "last"

    def test_format_symbol_empty(self) -> None:
        """Test formatting empty symbol."""
        printer = TreePrinter()
        assert printer._format_symbol("") == ""

    def test_format_symbol_with_color(self) -> None:
        """Test formatting symbol with color."""
        printer = TreePrinter(use_color=True)
        result = printer._format_symbol("+")

        assert COLOR_GREEN in result
        assert " " in result  # Has trailing space


class TestComplexTreeOutput:
    """Tests for complex tree structures."""

    def test_indexed_resources(self) -> None:
        """Test printing indexed resources."""
        resources = [
            {"address": 'aws_instance.web["a"]', "action": "created", "symbol": "+"},
            {"address": 'aws_instance.web["b"]', "action": "created", "symbol": "+"},
        ]
        graph = build_graph(resources)
        printer = TreePrinter(use_color=False)

        output = io.StringIO()
        with redirect_stdout(output):
            printer.print_tree(graph.get_tree())

        result = output.getvalue()
        assert "aws_instance" in result
        assert "web" in result

    def test_mixed_actions(self) -> None:
        """Test tree with mixed actions shows aggregate symbols."""
        resources = [
            {"address": "aws_instance.create", "action": "created", "symbol": "+"},
            {"address": "aws_instance.destroy", "action": "destroyed", "symbol": "-"},
        ]
        graph = build_graph(resources)
        printer = TreePrinter(use_color=False)

        output = io.StringIO()
        with redirect_stdout(output):
            printer.print_tree(graph.get_tree())

        result = output.getvalue()
        # Should have both symbols somewhere
        assert "+" in result
        assert "-" in result
