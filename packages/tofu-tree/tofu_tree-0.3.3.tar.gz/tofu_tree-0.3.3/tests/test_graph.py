"""Tests for the graph module."""

from __future__ import annotations

from tofu_tree.graph import (
    ACTION_SYMBOLS,
    ResourceGraph,
    build_graph,
    parse_plan_output,
)


class TestActionSymbols:
    """Tests for action symbol mapping."""

    def test_action_symbols_mapping(self) -> None:
        """Test that action symbols are correctly mapped."""
        assert ACTION_SYMBOLS["created"] == "+"
        assert ACTION_SYMBOLS["destroyed"] == "-"
        assert ACTION_SYMBOLS["replaced"] == "±"
        assert ACTION_SYMBOLS["updated"] == "~"

    def test_action_symbols_complete(self) -> None:
        """Test that all expected actions are present."""
        expected_actions = {"created", "destroyed", "replaced", "updated"}
        assert set(ACTION_SYMBOLS.keys()) == expected_actions


class TestParsePlanOutput:
    """Tests for parse_plan_output function."""

    def test_parse_basic_plan(self, sample_plan_output: list[str]) -> None:
        """Test parsing a basic plan output."""
        resources = parse_plan_output(sample_plan_output)

        assert len(resources) == 7
        assert resources[0]["address"] == "aws_instance.web"
        assert resources[0]["action"] == "created"
        assert resources[0]["symbol"] == "+"

    def test_parse_empty_input(self) -> None:
        """Test parsing empty input returns empty list."""
        assert parse_plan_output([]) == []

    def test_parse_no_changes(self) -> None:
        """Test parsing output with no changes."""
        lines = ["No changes. Infrastructure is up-to-date."]
        assert parse_plan_output(lines) == []

    def test_parse_ignores_lines_before_plan_section(self) -> None:
        """Test that lines before 'will perform' are ignored."""
        lines = [
            "  # some_resource.ignored will be created\n",
            "Terraform will perform the following actions:\n",
            "  # aws_instance.web will be created\n",
        ]
        resources = parse_plan_output(lines)

        assert len(resources) == 1
        assert resources[0]["address"] == "aws_instance.web"

    def test_parse_all_action_types(self) -> None:
        """Test parsing all action types."""
        lines = [
            "OpenTofu will perform the following actions:\n",
            "  # resource.create will be created\n",
            "  # resource.destroy will be destroyed\n",
            "  # resource.replace must be replaced\n",
            "  # resource.update will be updated\n",
        ]
        resources = parse_plan_output(lines)

        assert len(resources) == 4
        assert resources[0]["symbol"] == "+"
        assert resources[1]["symbol"] == "-"
        assert resources[2]["symbol"] == "±"
        assert resources[3]["symbol"] == "~"

    def test_parse_indexed_resources(self) -> None:
        """Test parsing resources with indexes."""
        lines = [
            "Terraform will perform the following actions:\n",
            '  # aws_instance.web["prod"] will be created\n',
            "  # aws_instance.web[0] will be created\n",
        ]
        resources = parse_plan_output(lines)

        assert len(resources) == 2
        assert 'aws_instance.web["prod"]' in resources[0]["address"]
        assert "aws_instance.web[0]" in resources[1]["address"]


class TestResourceGraph:
    """Tests for ResourceGraph class."""

    def test_empty_graph(self) -> None:
        """Test creating an empty graph."""
        graph = ResourceGraph()

        assert graph.get_tree() == {}
        assert graph.get_resources() == []

    def test_add_simple_resource(self) -> None:
        """Test adding a simple resource."""
        graph = ResourceGraph()
        resource = {"address": "aws_instance.web", "action": "created", "symbol": "+"}
        graph.add_resource(resource)

        assert len(graph.get_resources()) == 1
        assert "aws_instance" in graph.get_tree()

    def test_add_module_resource(self) -> None:
        """Test adding a module resource."""
        graph = ResourceGraph()
        resource = {
            "address": "module.vpc.aws_subnet.main",
            "action": "created",
            "symbol": "+",
        }
        graph.add_resource(resource)

        tree = graph.get_tree()
        assert "module.vpc" in tree

    def test_add_indexed_resource(self) -> None:
        """Test adding an indexed resource."""
        graph = ResourceGraph()
        resource = {
            "address": 'aws_instance.web["prod"]',
            "action": "created",
            "symbol": "+",
        }
        graph.add_resource(resource)

        tree = graph.get_tree()
        assert "aws_instance" in tree

    def test_get_resource_symbols_empty(self) -> None:
        """Test getting symbols from empty node."""
        symbols = ResourceGraph.get_resource_symbols({})
        assert symbols == []

    def test_get_resource_symbols_from_list(self) -> None:
        """Test getting symbols from a list node."""
        node = [
            {"resource": {"symbol": "+"}},
            {"resource": {"symbol": "-"}},
        ]
        symbols = ResourceGraph.get_resource_symbols(node)

        assert "+" in symbols
        assert "-" in symbols

    def test_get_aggregate_symbol_empty(self) -> None:
        """Test aggregate symbol for empty list."""
        assert ResourceGraph.get_aggregate_symbol([]) == ""

    def test_get_aggregate_symbol_priority(self) -> None:
        """Test aggregate symbol respects priority order."""
        # + has highest priority
        assert ResourceGraph.get_aggregate_symbol(["-", "+", "~"]) == "+"
        assert ResourceGraph.get_aggregate_symbol(["-", "~"]) == "-"
        assert ResourceGraph.get_aggregate_symbol(["~"]) == "~"

    def test_get_aggregate_symbol_unknown(self) -> None:
        """Test aggregate symbol for unknown symbols."""
        assert ResourceGraph.get_aggregate_symbol(["?"]) == "?"


class TestBuildGraph:
    """Tests for build_graph function."""

    def test_build_graph_empty(self) -> None:
        """Test building graph from empty list."""
        graph = build_graph([])

        assert graph.get_resources() == []
        assert graph.get_tree() == {}

    def test_build_graph_multiple_resources(
        self, sample_resources: list[dict[str, str]]
    ) -> None:
        """Test building graph from multiple resources."""
        graph = build_graph(sample_resources)

        assert len(graph.get_resources()) == len(sample_resources)

    def test_build_graph_preserves_order(self) -> None:
        """Test that resources are added in order."""
        resources = [
            {"address": "a.first", "action": "created", "symbol": "+"},
            {"address": "b.second", "action": "created", "symbol": "+"},
            {"address": "c.third", "action": "created", "symbol": "+"},
        ]
        graph = build_graph(resources)

        result_addresses = [r["address"] for r in graph.get_resources()]
        assert result_addresses == ["a.first", "b.second", "c.third"]


class TestComplexScenarios:
    """Tests for complex graph scenarios."""

    def test_multiple_resources_same_type(self) -> None:
        """Test multiple resources of the same type."""
        resources = [
            {"address": "aws_instance.a", "action": "created", "symbol": "+"},
            {"address": "aws_instance.b", "action": "destroyed", "symbol": "-"},
            {"address": "aws_instance.c", "action": "updated", "symbol": "~"},
        ]
        graph = build_graph(resources)
        tree = graph.get_tree()

        assert "aws_instance" in tree
        assert len(graph.get_resources()) == 3

    def test_nested_modules(self) -> None:
        """Test deeply nested module resources."""
        resources = [
            {
                "address": "module.level1.module.level2.aws_instance.deep",
                "action": "created",
                "symbol": "+",
            },
        ]
        graph = build_graph(resources)
        tree = graph.get_tree()

        # module.level1 should be in the tree
        assert any("module.level1" in k for k in tree)

    def test_mixed_indexed_and_simple(self) -> None:
        """Test mixing indexed and simple resources."""
        resources = [
            {"address": "aws_instance.simple", "action": "created", "symbol": "+"},
            {
                "address": 'aws_instance.indexed["a"]',
                "action": "created",
                "symbol": "+",
            },
            {
                "address": 'aws_instance.indexed["b"]',
                "action": "created",
                "symbol": "+",
            },
        ]
        graph = build_graph(resources)

        assert len(graph.get_resources()) == 3
