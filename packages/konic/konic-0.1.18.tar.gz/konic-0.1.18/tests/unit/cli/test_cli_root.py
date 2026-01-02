"""Unit tests for root CLI commands."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from konic.cli.root import app


class TestGetHost:
    """Test cases for get-host command."""

    def test_get_host_with_env_var(self):
        """Test get-host when KONIC_HOST is configured."""
        runner = CliRunner()
        with patch.dict("os.environ", {"KONIC_HOST": "https://api.example.com"}):
            result = runner.invoke(app, ["get-host"])
            assert result.exit_code == 0
            assert "https://api.example.com" in result.stdout

    def test_get_host_without_env_var(self):
        """Test get-host when KONIC_HOST is not configured."""
        runner = CliRunner()
        with patch.dict("os.environ", {}, clear=True):
            result = runner.invoke(app, ["get-host"])
            assert result.exit_code == 0
            assert "Not configured" in result.stdout


class TestInit:
    """Test cases for init command."""

    @patch("konic.cli.root.cookiecutter")
    def test_init_default_template(self, mock_cookiecutter):
        """Test init command with default template."""
        runner = CliRunner()
        result = runner.invoke(app, ["init"], input="\n")
        assert result.exit_code == 0
        mock_cookiecutter.assert_called_once()

    @patch("konic.cli.root.cookiecutter")
    def test_init_with_custom_template(self, mock_cookiecutter):
        """Test init command with custom template."""
        runner = CliRunner()
        result = runner.invoke(app, ["init", "--template", "full"], input="\n")
        assert result.exit_code == 0
        mock_cookiecutter.assert_called_once()

    @patch("konic.cli.root.cookiecutter")
    def test_init_with_callback_template(self, mock_cookiecutter):
        """Test init command with callback template."""
        runner = CliRunner()
        result = runner.invoke(app, ["init", "--template", "callback"], input="\n")
        assert result.exit_code == 0
        mock_cookiecutter.assert_called_once()


class TestCompile:
    """Test cases for compile command."""

    @patch("konic.cli.root.compile_artifact")
    def test_compile_valid_path(self, mock_compile):
        """Test compile command with valid path."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("test_agent").mkdir()
            result = runner.invoke(app, ["compile", "test_agent"])
            assert result.exit_code == 0
            mock_compile.assert_called_once()

    @patch("konic.cli.root.compile_artifact")
    def test_compile_with_absolute_path(self, mock_compile):
        """Test compile command with absolute path."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            agent_dir = Path("test_agent").absolute()
            agent_dir.mkdir()
            result = runner.invoke(app, ["compile", str(agent_dir)])
            assert result.exit_code == 0
            mock_compile.assert_called_once()


class TestCLIApp:
    """Test cases for CLI app configuration."""

    def test_app_no_args_shows_help(self):
        """Test that running with no args shows help.

        Note: Typer returns exit code 2 for no_args_is_help=True because
        it's technically a usage error (missing required command).
        """
        runner = CliRunner()
        result = runner.invoke(app, [])
        # Typer returns exit code 2 for no_args_is_help, not 0
        assert result.exit_code == 2
        assert "konic" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_app_help_flag(self):
        """Test --help flag."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "agent" in result.stdout
        assert "train" in result.stdout
        assert "data" in result.stdout
        assert "health" in result.stdout
