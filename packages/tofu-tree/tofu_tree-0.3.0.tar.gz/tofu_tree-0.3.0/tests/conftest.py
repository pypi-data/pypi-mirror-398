"""Pytest configuration and fixtures for tofu-tree tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_plan_output() -> list[str]:
    """Sample terraform plan output for testing."""
    return [
        "OpenTofu will perform the following actions:\n",
        "\n",
        "  # aws_instance.web will be created\n",
        "  # aws_instance.api will be created\n",
        "  # aws_instance.old will be destroyed\n",
        "  # aws_security_group.main will be updated in-place\n",
        '  # module.vpc.aws_subnet.public["a"] will be created\n',
        '  # module.vpc.aws_subnet.public["b"] will be created\n',
        '  # module.vpc.aws_subnet.private["a"] will be created\n',
    ]


@pytest.fixture
def sample_resources() -> list[dict[str, str]]:
    """Sample parsed resources for testing."""
    return [
        {"address": "aws_instance.web", "action": "created", "symbol": "+"},
        {"address": "aws_instance.api", "action": "created", "symbol": "+"},
        {"address": "aws_instance.old", "action": "destroyed", "symbol": "-"},
        {"address": "aws_security_group.main", "action": "updated", "symbol": "~"},
        {
            "address": 'module.vpc.aws_subnet.public["a"]',
            "action": "created",
            "symbol": "+",
        },
        {
            "address": 'module.vpc.aws_subnet.public["b"]',
            "action": "created",
            "symbol": "+",
        },
    ]


@pytest.fixture
def complex_plan_output() -> list[str]:
    """Complex terraform plan output with nested modules."""
    return [
        "Terraform will perform the following actions:\n",
        "\n",
        "  # local_file.config will be created\n",
        '  # local_file.configs["app"] will be created\n',
        '  # local_file.configs["db"] will be created\n',
        "  # module.app.aws_instance.main will be created\n",
        '  # module.app.aws_instance.workers["api"] will be created\n',
        '  # module.app.aws_instance.workers["web"] will be created\n',
        "  # module.db.aws_rds_instance.main will be destroyed\n",
        "  # module.db.aws_rds_instance.replica will be replaced\n",
    ]
