"""Unit tests for health CLI commands."""

from unittest.mock import patch

from typer.testing import CliRunner

from konic.cli.src.health import app


class TestHealthCheck:
    """Test cases for health check command.

    Note: The health app has only one command ('check'), so Typer converts it
    to a standalone command. We invoke without the 'check' subcommand.
    """

    @patch("konic.cli.src.health.client")
    def test_health_check_success(self, mock_client):
        """Test successful health check."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00",
        }

        # No 'check' argument needed - app IS the check command (single-command Typer)
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "healthy" in result.stdout.lower()

    @patch("konic.cli.src.health.client")
    def test_health_check_returns_json(self, mock_client):
        """Test health check returns JSON output."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "status": "healthy",
            "version": "1.0.0",
        }

        result = runner.invoke(app, [])
        assert result.exit_code == 0
        # Verify the output contains the health data
        assert "status" in result.stdout or "healthy" in result.stdout

    @patch("konic.cli.src.health.client")
    def test_health_check_with_connection_error(self, mock_client):
        """Test health check with connection error."""
        runner = CliRunner()
        mock_client.get_json.side_effect = ConnectionError("Connection failed")

        result = runner.invoke(app, [])
        assert result.exit_code == 1
