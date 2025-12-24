"""Tests for the CLI module."""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

from tofu_tree.cli import create_parser, find_terraform_command, main


class TestFindTerraformCommand:
    """Tests for find_terraform_command function."""

    def test_find_tofu(self) -> None:
        """Test finding tofu command."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = (
                lambda cmd: "/usr/bin/tofu" if cmd == "tofu" else None
            )
            result = find_terraform_command()
            assert result == "tofu"

    def test_find_terraform(self) -> None:
        """Test finding terraform command when tofu is not available."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: (
                "/usr/bin/terraform" if cmd == "terraform" else None
            )
            result = find_terraform_command()
            assert result == "terraform"

    def test_find_neither(self) -> None:
        """Test when neither command is available."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            result = find_terraform_command()
            assert result is None

    def test_prefers_tofu(self) -> None:
        """Test that tofu is preferred over terraform."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: f"/usr/bin/{cmd}"
            result = find_terraform_command()
            assert result == "tofu"


class TestCreateParser:
    """Tests for create_parser function."""

    def test_parser_creation(self) -> None:
        """Test parser is created successfully."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "tofu-tree"

    def test_parser_no_color_flag(self) -> None:
        """Test --no-color flag."""
        parser = create_parser()
        args = parser.parse_args(["--no-color"])
        assert args.no_color is True

    def test_parser_input_flag(self) -> None:
        """Test --input flag."""
        parser = create_parser()
        args = parser.parse_args(["--input"])
        assert args.input is True

    def test_parser_input_short_flag(self) -> None:
        """Test -i short flag."""
        parser = create_parser()
        args = parser.parse_args(["-i"])
        assert args.input is True

    def test_parser_path_argument(self) -> None:
        """Test path positional argument."""
        parser = create_parser()
        args = parser.parse_args(["/path/to/terraform"])
        assert args.path == "/path/to/terraform"

    def test_parser_default_values(self) -> None:
        """Test default values."""
        parser = create_parser()
        args = parser.parse_args([])
        assert args.no_color is False
        assert args.input is False
        assert args.path is None

    def test_parser_combined_flags(self) -> None:
        """Test combining multiple flags."""
        parser = create_parser()
        args = parser.parse_args(["--no-color", "--input"])
        assert args.no_color is True
        assert args.input is True


class TestMainFunction:
    """Tests for main function."""

    def test_main_with_stdin_input(self) -> None:
        """Test main with stdin input."""
        plan_output = """Terraform will perform the following actions:

  # aws_instance.web will be created
  # aws_instance.api will be created
"""
        with (
            patch("sys.argv", ["tofu-tree", "--input"]),
            patch("sys.stdin", io.StringIO(plan_output)),
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                main()

            result = output.getvalue()
            assert "aws_instance" in result
            assert "2 to be created" in result

    def test_main_no_resources(self) -> None:
        """Test main when no resources found."""
        plan_output = "No changes. Infrastructure is up-to-date."

        with (
            patch("sys.argv", ["tofu-tree", "--input"]),
            patch("sys.stdin", io.StringIO(plan_output)),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1

    def test_main_with_color_disabled(self) -> None:
        """Test main with --no-color flag."""
        plan_output = """Terraform will perform the following actions:

  # aws_instance.web will be created
"""
        with (
            patch("sys.argv", ["tofu-tree", "--input", "--no-color"]),
            patch("sys.stdin", io.StringIO(plan_output)),
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                main()

            result = output.getvalue()
            # Should not contain ANSI codes
            assert "\033[" not in result

    def test_main_with_color_enabled(self) -> None:
        """Test main with color (default)."""
        plan_output = """Terraform will perform the following actions:

  # aws_instance.web will be created
"""
        with (
            patch("sys.argv", ["tofu-tree", "--input"]),
            patch("sys.stdin", io.StringIO(plan_output)),
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                main()

            result = output.getvalue()
            # Should contain ANSI codes
            assert "\033[" in result


class TestMainWithPlanCommand:
    """Tests for main function with plan command execution."""

    def test_main_no_terraform_command(self) -> None:
        """Test main when no terraform/tofu command is found."""
        with (
            patch("sys.argv", ["tofu-tree"]),
            patch("shutil.which", return_value=None),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1

    def test_main_invalid_path(self) -> None:
        """Test main with invalid path."""
        with (
            patch("sys.argv", ["tofu-tree", "/nonexistent/path"]),
            patch("shutil.which", return_value="/usr/bin/tofu"),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1
