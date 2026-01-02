"""Unit tests for artifact CLI commands."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from konic.cli.src.artifacts import app
from konic.common.errors import KonicHTTPError


class TestArtifactList:
    """Test cases for artifact list command."""

    @patch("konic.cli.src.artifacts.resolve_agent_identifier")
    @patch("konic.cli.src.artifacts.client")
    def test_list_artifacts_success(self, mock_client, mock_resolve):
        """Test successful artifact listing."""
        runner = CliRunner()
        mock_resolve.return_value = "agent-123"
        mock_client.get_json.side_effect = [
            {"agent_name": "test-agent"},
            [
                {
                    "id": "artifact-123",
                    "artifact_type": "final",
                    "iteration": 1000,
                    "training_job_id": "job-123",
                    "file_size": 1024000,
                    "created_at": "2024-01-01T00:00:00",
                }
            ],
        ]

        result = runner.invoke(app, ["list", "test-agent"])
        assert result.exit_code == 0
        assert "test-agent" in result.stdout

    @patch("konic.cli.src.artifacts.resolve_agent_identifier")
    @patch("konic.cli.src.artifacts.client")
    def test_list_artifacts_empty(self, mock_client, mock_resolve):
        """Test artifact listing with no artifacts."""
        runner = CliRunner()
        mock_resolve.return_value = "agent-123"
        mock_client.get_json.side_effect = [
            {"agent_name": "test-agent"},
            [],
        ]

        result = runner.invoke(app, ["list", "test-agent"])
        assert result.exit_code == 0
        assert "No artifacts found" in result.stdout

    @patch("konic.cli.src.artifacts.resolve_agent_identifier")
    @patch("konic.cli.src.artifacts.client")
    def test_list_artifacts_by_job(self, mock_client, mock_resolve):
        """Test artifact listing filtered by job ID."""
        runner = CliRunner()
        mock_resolve.return_value = "agent-123"
        mock_client.get_json.side_effect = [
            {"agent_name": "test-agent"},
            [
                {
                    "id": "artifact-123",
                    "artifact_type": "checkpoint",
                    "iteration": 500,
                    "training_job_id": "job-123",
                    "file_size": 512000,
                    "created_at": "2024-01-01T00:00:00",
                }
            ],
        ]

        result = runner.invoke(app, ["list", "test-agent", "--job-id", "job-123"])
        assert result.exit_code == 0

    @patch("konic.cli.src.artifacts.resolve_agent_identifier")
    @patch("konic.cli.src.artifacts.client")
    def test_list_artifacts_by_type(self, mock_client, mock_resolve):
        """Test artifact listing filtered by type."""
        runner = CliRunner()
        mock_resolve.return_value = "agent-123"
        mock_client.get_json.side_effect = [
            {"agent_name": "test-agent"},
            [
                {
                    "id": "artifact-123",
                    "artifact_type": "final",
                    "iteration": 1000,
                    "file_size": 1024000,
                    "created_at": "2024-01-01T00:00:00",
                },
                {
                    "id": "artifact-124",
                    "artifact_type": "checkpoint",
                    "iteration": 500,
                    "file_size": 512000,
                    "created_at": "2024-01-01T00:00:00",
                },
            ],
        ]

        result = runner.invoke(app, ["list", "test-agent", "--type", "final"])
        assert result.exit_code == 0

    @patch("konic.cli.src.artifacts.resolve_agent_identifier")
    @patch("konic.cli.src.artifacts.client")
    def test_list_artifacts_json_output(self, mock_client, mock_resolve):
        """Test artifact listing with JSON output."""
        runner = CliRunner()
        mock_resolve.return_value = "agent-123"
        mock_client.get_json.side_effect = [
            {"agent_name": "test-agent"},
            [{"id": "artifact-123"}],
        ]

        result = runner.invoke(app, ["list", "test-agent", "--json"])
        assert result.exit_code == 0


class TestArtifactShow:
    """Test cases for artifact show command."""

    @patch("konic.cli.src.artifacts.client")
    def test_show_artifact_success(self, mock_client):
        """Test successful artifact details retrieval."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "id": "artifact-123",
            "agent_name": "test-agent",
            "agent_id": "agent-123",
            "training_job_id": "job-123",
            "artifact_type": "final",
            "iteration": 1000,
            "file_size": 1024000,
            "checksum_sha256": "abc123def456",
            "created_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["show", "artifact-123"])
        assert result.exit_code == 0
        assert "test-agent" in result.stdout

    @patch("konic.cli.src.artifacts.client")
    def test_show_artifact_not_found(self, mock_client):
        """Test artifact show when artifact not found."""
        runner = CliRunner()
        mock_client.get_json.side_effect = KonicHTTPError(
            status_code=404, message="Not Found", endpoint="/artifacts/artifact-123"
        )

        result = runner.invoke(app, ["show", "artifact-123"])
        assert result.exit_code == 1

    @patch("konic.cli.src.artifacts.client")
    def test_show_artifact_json_output(self, mock_client):
        """Test artifact show with JSON output."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "id": "artifact-123",
            "artifact_type": "checkpoint",
        }

        result = runner.invoke(app, ["show", "artifact-123", "--json"])
        assert result.exit_code == 0


class TestArtifactDownload:
    """Test cases for artifact download command."""

    @patch("konic.cli.src.artifacts.client")
    def test_download_artifact_success(self, mock_client):
        """Test successful artifact download."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "download_url": "https://example.com/artifact.zip",
            "artifact_type": "final",
            "iteration": 1000,
            "file_size": 1024000,
            "checksum_sha256": "abc123def456",
        }
        mock_client.download_file_with_progress.return_value = (
            Path("final_001000.zip"),
            "abc123def456",
        )

        with runner.isolated_filesystem():
            result = runner.invoke(app, ["download", "artifact-123"])
            assert result.exit_code == 0
            assert "Downloaded successfully" in result.stdout

    @patch("konic.cli.src.artifacts.client")
    def test_download_artifact_with_output_path(self, mock_client):
        """Test artifact download with custom output path."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "download_url": "https://example.com/artifact.zip",
            "artifact_type": "checkpoint",
            "iteration": 500,
            "file_size": 512000,
            "checksum_sha256": "def456abc123",
        }
        mock_client.download_file_with_progress.return_value = (
            Path("checkpoints/checkpoint_000500.zip"),
            "def456abc123",
        )

        with runner.isolated_filesystem():
            Path("checkpoints").mkdir()
            result = runner.invoke(app, ["download", "artifact-123", "--output", "checkpoints"])
            assert result.exit_code == 0

    @patch("konic.cli.src.artifacts.client")
    def test_download_artifact_skip_verify(self, mock_client):
        """Test artifact download with skip verify."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "download_url": "https://example.com/artifact.zip",
            "artifact_type": "final",
            "iteration": 1000,
            "file_size": 1024000,
            "checksum_sha256": "abc123def456",
        }
        mock_client.download_file_with_progress.return_value = (
            Path("final_001000.zip"),
            "abc123def456",
        )

        with runner.isolated_filesystem():
            result = runner.invoke(app, ["download", "artifact-123", "--skip-verify"])
            assert result.exit_code == 0
            assert "skipped" in result.stdout.lower()

    @patch("konic.cli.src.artifacts.client")
    def test_download_artifact_not_found(self, mock_client):
        """Test artifact download when artifact not found."""
        runner = CliRunner()
        mock_client.get_json.side_effect = KonicHTTPError(
            status_code=404, message="Not Found", endpoint="/artifacts/artifact-123/download"
        )

        with runner.isolated_filesystem():
            result = runner.invoke(app, ["download", "artifact-123"])
            assert result.exit_code == 1

    @patch("konic.cli.src.artifacts.client")
    def test_download_artifact_checksum_mismatch(self, mock_client):
        """Test artifact download with checksum mismatch."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "download_url": "https://example.com/artifact.zip",
            "artifact_type": "final",
            "iteration": 1000,
            "file_size": 1024000,
            "checksum_sha256": "abc123def456",
        }
        mock_client.download_file_with_progress.side_effect = ValueError("Checksum mismatch")

        with runner.isolated_filesystem():
            result = runner.invoke(app, ["download", "artifact-123"])
            assert result.exit_code == 1

    @patch("konic.cli.src.artifacts.client")
    def test_download_artifact_with_host_override(self, mock_client):
        """Test artifact download with host override."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "download_url": "https://example.com/artifact.zip",
            "artifact_type": "final",
            "iteration": 1000,
            "file_size": 1024000,
            "checksum_sha256": "abc123def456",
        }
        mock_client.download_file_with_progress.return_value = (
            Path("final_001000.zip"),
            "abc123def456",
        )

        with runner.isolated_filesystem():
            result = runner.invoke(
                app, ["download", "artifact-123", "--host", "https://custom.api.com"]
            )
            assert result.exit_code == 0
            mock_client.set_base_url.assert_called_with("https://custom.api.com")
