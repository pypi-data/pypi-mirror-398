"""Unit tests for inference CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from konic.cli.src.inference import app
from konic.common.errors import KonicHTTPError


class TestInferenceStart:
    """Test cases for inference start command."""

    @patch("konic.cli.src.inference.client")
    def test_start_server_success(self, mock_client):
        """Test successful inference server start."""
        runner = CliRunner()
        mock_client.post_json.return_value = {
            "id": "server-123",
            "artifact_id": "art_a1b2c3d4",
            "agent_name": "test-agent",
            "agent_id": "agent-123",
            "training_job_id": "job-123",
            "iteration": 1000,
            "server_type": "http",
            "status": "pending",
            "container_name": "test-container",
            "external_url": "https://test.example.com",
            "external_port": 8080,
            "auto_stop_minutes": None,
            "created_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["start", "art_a1b2c3d4"])
        assert result.exit_code == 0
        assert "started successfully" in result.stdout.lower()

    @patch("konic.cli.src.inference.client")
    def test_start_server_with_websocket_type(self, mock_client):
        """Test inference server start with websocket type."""
        runner = CliRunner()
        mock_client.post_json.return_value = {
            "id": "server-123",
            "artifact_id": "art_a1b2c3d4",
            "server_type": "websocket",
            "status": "pending",
            "created_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["start", "art_a1b2c3d4", "--type", "websocket"])
        assert result.exit_code == 0

    @patch("konic.cli.src.inference.client")
    def test_start_server_with_auto_stop(self, mock_client):
        """Test inference server start with auto-stop."""
        runner = CliRunner()
        mock_client.post_json.return_value = {
            "id": "server-123",
            "artifact_id": "art_a1b2c3d4",
            "server_type": "http",
            "status": "pending",
            "auto_stop_minutes": 30,
            "created_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["start", "art_a1b2c3d4", "--auto-stop", "30"])
        assert result.exit_code == 0
        assert "30 minutes" in result.stdout

    @patch("konic.cli.src.inference._wait_for_server_ready")
    @patch("konic.cli.src.inference.client")
    def test_start_server_with_wait(self, mock_client, mock_wait):
        """Test inference server start with wait flag."""
        runner = CliRunner()
        mock_client.post_json.return_value = {
            "id": "server-123",
            "artifact_id": "art_a1b2c3d4",
            "server_type": "http",
            "status": "pending",
            "created_at": "2024-01-01T00:00:00",
        }
        mock_wait.return_value = True

        result = runner.invoke(app, ["start", "art_a1b2c3d4", "--wait"])
        assert result.exit_code == 0
        mock_wait.assert_called_once()

    def test_start_server_invalid_type(self):
        """Test inference server start with invalid type."""
        runner = CliRunner()

        result = runner.invoke(app, ["start", "art_a1b2c3d4", "--type", "invalid"])
        assert result.exit_code == 1
        assert "Invalid server type" in result.stdout


class TestInferenceList:
    """Test cases for inference list command."""

    @patch("konic.cli.src.inference.client")
    def test_list_servers_success(self, mock_client):
        """Test successful server listing."""
        runner = CliRunner()
        mock_client.get_json.return_value = [
            {
                "id": "server-123",
                "agent_name": "test-agent",
                "artifact_id": "art_a1b2c3d4",
                "server_type": "http",
                "status": "running",
                "request_count": 100,
                "created_at": "2024-01-01T00:00:00",
            }
        ]

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "test-agent" in result.stdout

    @patch("konic.cli.src.inference.client")
    def test_list_servers_empty(self, mock_client):
        """Test server listing with no servers."""
        runner = CliRunner()
        mock_client.get_json.return_value = []

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No inference servers found" in result.stdout

    @patch("konic.cli.src.inference.client")
    def test_list_servers_with_filters(self, mock_client):
        """Test server listing with filters."""
        runner = CliRunner()
        mock_client.get_json.return_value = []

        result = runner.invoke(
            app,
            [
                "list",
                "--status",
                "running",
                "--agent",
                "test-agent",
                "--artifact",
                "art_123",
                "--type",
                "http",
            ],
        )
        assert result.exit_code == 0

    @patch("konic.cli.src.inference.client")
    def test_list_servers_active_only(self, mock_client):
        """Test listing only active servers."""
        runner = CliRunner()
        mock_client.get_json.return_value = [
            {
                "id": "server-123",
                "status": "running",
                "created_at": "2024-01-01T00:00:00",
            }
        ]

        result = runner.invoke(app, ["list", "--active"])
        assert result.exit_code == 0

    @patch("konic.cli.src.inference.client")
    def test_list_servers_json_output(self, mock_client):
        """Test server listing with JSON output."""
        runner = CliRunner()
        mock_client.get_json.return_value = [{"id": "server-123"}]

        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0

    def test_list_servers_invalid_order(self):
        """Test server listing with invalid order."""
        runner = CliRunner()

        result = runner.invoke(app, ["list", "--order", "invalid"])
        assert result.exit_code == 1
        assert "Invalid order" in result.stdout


class TestInferenceStatus:
    """Test cases for inference status command."""

    @patch("konic.cli.src.inference.client")
    def test_get_status_success(self, mock_client):
        """Test successful status retrieval."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "id": "server-123",
            "status": "running",
            "container_status": "healthy",
            "internal_url": "http://internal:8000",
            "external_url": "https://test.example.com",
            "uptime_seconds": 3600,
            "request_count": 100,
        }

        result = runner.invoke(app, ["status", "server-123"])
        assert result.exit_code == 0
        assert "running" in result.stdout

    @patch("konic.cli.src.inference.client")
    def test_get_status_not_found(self, mock_client):
        """Test status retrieval when server not found."""
        runner = CliRunner()
        mock_client.get_json.side_effect = KonicHTTPError(
            status_code=404, message="Not Found", endpoint="/inference/server-123/status"
        )

        result = runner.invoke(app, ["status", "server-123"])
        assert result.exit_code == 1

    @patch("konic.cli.src.inference.client")
    def test_get_status_json_output(self, mock_client):
        """Test status retrieval with JSON output."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "id": "server-123",
            "status": "running",
        }

        result = runner.invoke(app, ["status", "server-123", "--json"])
        assert result.exit_code == 0


class TestInferenceStop:
    """Test cases for inference stop command."""

    @patch("konic.cli.src.inference.client")
    def test_stop_server_with_force(self, mock_client):
        """Test server stop with force flag."""
        runner = CliRunner()

        result = runner.invoke(app, ["stop", "server-123", "--force"])
        assert result.exit_code == 0
        mock_client.delete_json.assert_called_once_with("/inference/server-123")

    @patch("konic.cli.src.inference.client")
    def test_stop_server_with_confirmation(self, mock_client):
        """Test server stop with confirmation."""
        runner = CliRunner()

        result = runner.invoke(app, ["stop", "server-123"], input="y\n")
        assert result.exit_code == 0
        mock_client.delete_json.assert_called_once()

    @patch("konic.cli.src.inference.client")
    def test_stop_server_cancelled(self, mock_client):
        """Test server stop cancelled by user."""
        runner = CliRunner()

        result = runner.invoke(app, ["stop", "server-123"], input="n\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.stdout

    @patch("konic.cli.src.inference.client")
    def test_stop_server_not_found(self, mock_client):
        """Test server stop when server not found."""
        runner = CliRunner()
        mock_client.delete_json.side_effect = KonicHTTPError(
            status_code=404, message="Not Found", endpoint="/inference/server-123"
        )

        result = runner.invoke(app, ["stop", "server-123", "--force"])
        assert result.exit_code == 1


class TestInferenceLogs:
    """Test cases for inference logs command."""

    @patch("konic.cli.src.inference.client")
    def test_get_logs_success(self, mock_client):
        """Test successful log retrieval."""
        runner = CliRunner()
        mock_client.get_json.return_value = {"logs": "line1\nline2\nline3"}

        result = runner.invoke(app, ["logs", "server-123"])
        assert result.exit_code == 0
        assert "line1" in result.stdout

    @patch("konic.cli.src.inference.client")
    def test_get_logs_with_tail(self, mock_client):
        """Test log retrieval with tail option."""
        runner = CliRunner()
        mock_client.get_json.return_value = {"logs": "line1\nline2"}

        result = runner.invoke(app, ["logs", "server-123", "--tail", "50"])
        assert result.exit_code == 0

    @patch("konic.cli.src.inference._follow_logs")
    @patch("konic.cli.src.inference.client")
    def test_get_logs_with_follow(self, mock_client, mock_follow):
        """Test log retrieval with follow flag."""
        runner = CliRunner()

        result = runner.invoke(app, ["logs", "server-123", "--follow"])
        assert result.exit_code == 0
        mock_follow.assert_called_once()

    @patch("konic.cli.src.inference.client")
    def test_get_logs_not_found(self, mock_client):
        """Test log retrieval when server not found."""
        runner = CliRunner()
        mock_client.get_json.side_effect = KonicHTTPError(
            status_code=404, message="Not Found", endpoint="/inference/server-123/logs"
        )

        result = runner.invoke(app, ["logs", "server-123"])
        assert result.exit_code == 1

    @patch("konic.cli.src.inference.client")
    def test_get_logs_empty(self, mock_client):
        """Test log retrieval with empty logs."""
        runner = CliRunner()
        mock_client.get_json.return_value = {"logs": ""}

        result = runner.invoke(app, ["logs", "server-123"])
        assert result.exit_code == 0
        assert "No logs available" in result.stdout


class TestInferencePredict:
    """Test cases for inference predict command."""

    @patch("konic.cli.src.inference._get_external_client")
    @patch("konic.cli.src.inference.client")
    def test_predict_success(self, mock_client, mock_get_external):
        """Test successful prediction."""
        runner = CliRunner()
        mock_external_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"action": [1, 0]}
        mock_external_client.post.return_value = mock_response

        mock_get_external.return_value = (
            mock_external_client,
            {"server_type": "http", "external_url": "https://test.example.com"},
        )

        result = runner.invoke(app, ["predict", "server-123", "--observation", "[0.1, 0.2, 0.3]"])
        assert result.exit_code == 0

    @patch("konic.cli.src.inference._get_external_client")
    def test_predict_from_file(self, mock_get_external):
        """Test prediction from file."""
        runner = CliRunner()
        mock_external_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"action": [1, 0]}
        mock_external_client.post.return_value = mock_response

        mock_get_external.return_value = (
            mock_external_client,
            {"server_type": "http", "external_url": "https://test.example.com"},
        )

        with runner.isolated_filesystem():
            obs_file = Path("obs.json")
            obs_file.write_text("[0.1, 0.2, 0.3]")

            result = runner.invoke(app, ["predict", "server-123", "--file", "obs.json"])
            assert result.exit_code == 0

    @patch("konic.cli.src.inference._get_external_client")
    def test_predict_deterministic(self, mock_get_external):
        """Test prediction with deterministic flag."""
        runner = CliRunner()
        mock_external_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"action": [1, 0]}
        mock_external_client.post.return_value = mock_response

        mock_get_external.return_value = (
            mock_external_client,
            {"server_type": "http", "external_url": "https://test.example.com"},
        )

        result = runner.invoke(
            app, ["predict", "server-123", "--observation", "[0.1, 0.2]", "--deterministic"]
        )
        assert result.exit_code == 0

    def test_predict_no_observation(self):
        """Test prediction without observation."""
        runner = CliRunner()

        result = runner.invoke(app, ["predict", "server-123"])
        assert result.exit_code == 1
        assert "Must provide --observation or --file" in result.stdout

    def test_predict_both_observation_and_file(self):
        """Test prediction with both observation and file."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            obs_file = Path("obs.json")
            obs_file.write_text("[0.1, 0.2]")

            result = runner.invoke(
                app, ["predict", "server-123", "--observation", "[0.1, 0.2]", "--file", "obs.json"]
            )
            assert result.exit_code == 1
            assert "Cannot use both" in result.stdout

    @patch("konic.cli.src.inference._get_external_client")
    def test_predict_websocket_server(self, mock_get_external):
        """Test prediction on websocket server."""
        runner = CliRunner()
        mock_get_external.return_value = (
            MagicMock(),
            {"server_type": "websocket", "external_url": "wss://test.example.com"},
        )

        result = runner.invoke(app, ["predict", "server-123", "--observation", "[0.1, 0.2]"])
        assert result.exit_code == 1
        assert "WebSocket" in result.stdout

    @patch("konic.cli.src.inference._get_external_client")
    def test_predict_invalid_json(self, mock_get_external):
        """Test prediction with invalid JSON."""
        runner = CliRunner()

        result = runner.invoke(app, ["predict", "server-123", "--observation", "invalid"])
        assert result.exit_code == 1
        assert "Invalid JSON" in result.stdout

    @patch("konic.cli.src.inference._get_external_client")
    def test_predict_http_error(self, mock_get_external):
        """Test prediction with HTTP error."""
        runner = CliRunner()
        mock_external_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal error"}
        mock_external_client.post.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )

        mock_get_external.return_value = (
            mock_external_client,
            {"server_type": "http", "external_url": "https://test.example.com"},
        )

        result = runner.invoke(app, ["predict", "server-123", "--observation", "[0.1, 0.2]"])
        assert result.exit_code == 1


class TestInferenceInfo:
    """Test cases for inference info command."""

    @patch("konic.cli.src.inference._get_external_client")
    def test_get_info_success(self, mock_get_external):
        """Test successful model info retrieval."""
        runner = CliRunner()
        mock_external_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "loaded": True,
            "artifact_id": "art_a1b2c3d4",
            "agent_name": "test-agent",
            "observation_space": {"shape": [4]},
            "action_space": {"n": 2},
        }
        mock_external_client.get.return_value = mock_response

        mock_get_external.return_value = (
            mock_external_client,
            {"server_type": "http", "external_url": "https://test.example.com"},
        )

        result = runner.invoke(app, ["info", "server-123"])
        assert result.exit_code == 0

    @patch("konic.cli.src.inference._get_external_client")
    def test_get_info_json_output(self, mock_get_external):
        """Test model info with JSON output."""
        runner = CliRunner()
        mock_external_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"loaded": True}
        mock_external_client.get.return_value = mock_response

        mock_get_external.return_value = (
            mock_external_client,
            {"server_type": "http", "external_url": "https://test.example.com"},
        )

        result = runner.invoke(app, ["info", "server-123", "--json"])
        assert result.exit_code == 0

    @patch("konic.cli.src.inference._get_external_client")
    def test_get_info_http_error(self, mock_get_external):
        """Test model info with HTTP error."""
        runner = CliRunner()
        mock_external_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_external_client.get.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )

        mock_get_external.return_value = (
            mock_external_client,
            {"server_type": "http", "external_url": "https://test.example.com"},
        )

        result = runner.invoke(app, ["info", "server-123"])
        assert result.exit_code == 1
