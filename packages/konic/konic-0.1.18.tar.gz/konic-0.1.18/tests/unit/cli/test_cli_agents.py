"""Unit tests for agent CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from konic.cli.src.agents import app
from konic.common.errors import KonicHTTPError


class TestAgentPush:
    """Test cases for agent push command."""

    @patch("konic.cli.src.agents._compile_agent_directory")
    @patch("konic.cli.src.agents.client")
    def test_push_agent_success(self, mock_client, mock_compile):
        """Test successful agent push."""
        runner = CliRunner()
        mock_compile.return_value = Path("/tmp/agent.zip")
        mock_client.upload_file_json.return_value = {
            "agent_name": "test-agent",
            "id": "123",
            "agent_version": "v1",
            "konic_version": "0.1.0",
            "file_size": 1024,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        with runner.isolated_filesystem():
            Path("test_agent").mkdir()
            result = runner.invoke(app, ["push", "test_agent"])
            assert result.exit_code == 0
            assert "pushed successfully" in result.stdout.lower()
            assert "test-agent" in result.stdout
            assert "123" in result.stdout
            assert "v1" in result.stdout
            # Verify mock was called correctly
            mock_client.upload_file_json.assert_called_once_with(
                "/agents/upload", Path("/tmp/agent.zip")
            )

    @patch("konic.cli.src.agents._compile_agent_directory")
    @patch("konic.cli.src.agents.client")
    def test_push_agent_conflict(self, mock_client, mock_compile):
        """Test agent push with name conflict."""
        runner = CliRunner()
        mock_compile.return_value = Path("/tmp/agent.zip")
        mock_client.upload_file_json.side_effect = KonicHTTPError(
            status_code=409,
            message="Conflict",
            endpoint="/agents/upload",
            response_body='{"detail": {"agent_name": "test-agent"}}',
        )

        with runner.isolated_filesystem():
            Path("test_agent").mkdir()
            result = runner.invoke(app, ["push", "test_agent"])
            assert result.exit_code == 1
            # Verify error message mentions the conflict
            assert "conflict" in result.stdout.lower() or "already exists" in result.stdout.lower()

    @patch("konic.cli.src.agents._compile_agent_directory")
    @patch("konic.cli.src.agents.client")
    def test_push_agent_with_host_override(self, mock_client, mock_compile):
        """Test agent push with host override."""
        runner = CliRunner()
        mock_compile.return_value = Path("/tmp/agent.zip")
        mock_client.upload_file_json.return_value = {
            "agent_name": "test-agent",
            "id": "123",
            "agent_version": "v1",
            "konic_version": "0.1.0",
            "file_size": 1024,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        with runner.isolated_filesystem():
            Path("test_agent").mkdir()
            result = runner.invoke(app, ["push", "test_agent", "--host", "https://custom.api.com"])
            assert result.exit_code == 0
            mock_client.set_base_url.assert_called_with("https://custom.api.com")

    @patch("konic.cli.src.agents._compile_agent_directory")
    @patch("konic.cli.src.agents.client")
    def test_push_agent_keep_artifact(self, mock_client, mock_compile):
        """Test agent push with keep-artifact flag keeps the zip file."""
        runner = CliRunner()
        mock_zip = MagicMock(spec=Path)
        mock_zip.exists.return_value = True
        mock_compile.return_value = mock_zip
        mock_client.upload_file_json.return_value = {
            "agent_name": "test-agent",
            "id": "123",
            "agent_version": "v1",
            "konic_version": "0.1.0",
            "file_size": 1024,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        with runner.isolated_filesystem():
            Path("test_agent").mkdir()
            result = runner.invoke(app, ["push", "test_agent", "--keep-artifact"])
            assert result.exit_code == 0
            mock_zip.unlink.assert_not_called()

    @patch("konic.cli.src.agents._compile_agent_directory")
    @patch("konic.cli.src.agents.client")
    def test_push_agent_cleanup_artifact_by_default(self, mock_client, mock_compile):
        """Test agent push cleans up artifact by default (without --keep-artifact)."""
        runner = CliRunner()
        mock_zip = MagicMock(spec=Path)
        mock_zip.exists.return_value = True
        mock_compile.return_value = mock_zip
        mock_client.upload_file_json.return_value = {
            "agent_name": "test-agent",
            "id": "123",
            "agent_version": "v1",
            "konic_version": "0.1.0",
            "file_size": 1024,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        with runner.isolated_filesystem():
            Path("test_agent").mkdir()
            result = runner.invoke(app, ["push", "test_agent"])
            assert result.exit_code == 0
            # Verify artifact is deleted when --keep-artifact is not used
            mock_zip.unlink.assert_called_once()


class TestAgentUpdate:
    """Test cases for agent update command."""

    @patch("konic.cli.src.agents._compile_agent_directory")
    @patch("konic.cli.src.agents.resolve_agent_identifier")
    @patch("konic.cli.src.agents.get_agent_by_id")
    @patch("konic.cli.src.agents.client")
    def test_update_agent_success(self, mock_client, mock_get_agent, mock_resolve, mock_compile):
        """Test successful agent update."""
        runner = CliRunner()
        mock_resolve.return_value = "123"
        mock_get_agent.return_value = {"agent_version": "v1"}
        mock_compile.return_value = Path("/tmp/agent.zip")
        mock_client.upload_file_json.return_value = {
            "agent_name": "test-agent",
            "id": "123",
            "agent_version": "v2",
            "konic_version": "0.1.0",
            "file_size": 1024,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        with runner.isolated_filesystem():
            Path("test_agent").mkdir()
            result = runner.invoke(app, ["update", "test_agent", "--agent", "test-agent"])
            assert result.exit_code == 0
            assert "updated successfully" in result.stdout.lower()

    @patch("konic.cli.src.agents._compile_agent_directory")
    @patch("konic.cli.src.agents.resolve_agent_identifier")
    @patch("konic.cli.src.agents.get_agent_by_id")
    @patch("konic.cli.src.agents.client")
    def test_update_agent_not_found(self, mock_client, mock_get_agent, mock_resolve, mock_compile):
        """Test agent update when agent not found."""
        runner = CliRunner()
        mock_resolve.return_value = "123"
        mock_get_agent.return_value = {"agent_version": "v1"}
        mock_compile.return_value = Path("/tmp/agent.zip")
        mock_client.upload_file_json.side_effect = KonicHTTPError(
            status_code=404, message="Not Found", endpoint="/agents/123/versions"
        )

        with runner.isolated_filesystem():
            Path("test_agent").mkdir()
            result = runner.invoke(app, ["update", "test_agent", "--agent", "test-agent"])
            assert result.exit_code == 1


class TestAgentList:
    """Test cases for agent list command."""

    @patch("konic.cli.src.agents.client")
    def test_list_agents_success(self, mock_client):
        """Test successful agent listing."""
        runner = CliRunner()
        mock_client.get_json.return_value = [
            {
                "agent_name": "agent1",
                "id": "123",
                "agent_version": "v1",
                "konic_version": "0.1.0",
                "file_size": 1024,
                "updated_at": "2024-01-01T00:00:00",
            }
        ]

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "agent1" in result.stdout

    @patch("konic.cli.src.agents.client")
    def test_list_agents_empty(self, mock_client):
        """Test agent listing with no agents."""
        runner = CliRunner()
        mock_client.get_json.return_value = []

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No agents found" in result.stdout

    @patch("konic.cli.src.agents.client")
    def test_list_agents_with_filters(self, mock_client):
        """Test agent listing with filters."""
        runner = CliRunner()
        mock_client.get_json.return_value = []

        result = runner.invoke(
            app,
            ["list", "--name", "test", "--konic-version", "0.1.0", "--start", "0", "--end", "10"],
        )
        assert result.exit_code == 0
        mock_client.get_json.assert_called_once()

    @patch("konic.cli.src.agents.client")
    def test_list_agents_json_output(self, mock_client):
        """Test agent listing with JSON output."""
        runner = CliRunner()
        mock_client.get_json.return_value = [{"agent_name": "agent1", "id": "123"}]

        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0


class TestAgentGet:
    """Test cases for agent get command."""

    @patch("konic.cli.src.agents.get_agent_by_id")
    def test_get_agent_success(self, mock_get_agent):
        """Test successful agent get."""
        runner = CliRunner()
        mock_get_agent.return_value = {
            "agent_name": "test-agent",
            "id": "123",
            "agent_version": "v1",
            "konic_version": "0.1.0",
            "file_size": 1024,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["get", "123"])
        assert result.exit_code == 0
        assert "test-agent" in result.stdout

    @patch("konic.cli.src.agents.get_agent_by_id")
    def test_get_agent_json_output(self, mock_get_agent):
        """Test agent get with JSON output."""
        runner = CliRunner()
        mock_get_agent.return_value = {"agent_name": "test-agent", "id": "123"}

        result = runner.invoke(app, ["get", "123", "--json"])
        assert result.exit_code == 0


class TestAgentDelete:
    """Test cases for agent delete command."""

    @patch("konic.cli.src.agents.resolve_agent_identifier")
    @patch("konic.cli.src.agents.get_agent_by_id")
    @patch("konic.cli.src.agents.client")
    def test_delete_agent_success_with_force(self, mock_client, mock_get_agent, mock_resolve):
        """Test successful agent delete with force flag."""
        runner = CliRunner()
        mock_resolve.return_value = "123"
        mock_get_agent.return_value = {"agent_name": "test-agent"}

        result = runner.invoke(app, ["delete", "--agent", "test-agent", "--force"])
        assert result.exit_code == 0
        mock_client.delete.assert_called_once_with("/agents/123")

    @patch("konic.cli.src.agents.resolve_agent_identifier")
    @patch("konic.cli.src.agents.get_agent_by_id")
    @patch("konic.cli.src.agents.client")
    def test_delete_agent_with_confirmation(self, mock_client, mock_get_agent, mock_resolve):
        """Test agent delete with confirmation."""
        runner = CliRunner()
        mock_resolve.return_value = "123"
        mock_get_agent.return_value = {"agent_name": "test-agent"}

        result = runner.invoke(app, ["delete", "--agent", "test-agent"], input="y\n")
        assert result.exit_code == 0
        mock_client.delete.assert_called_once()

    @patch("konic.cli.src.agents.resolve_agent_identifier")
    @patch("konic.cli.src.agents.get_agent_by_id")
    def test_delete_agent_cancelled(self, mock_get_agent, mock_resolve):
        """Test agent delete cancelled by user."""
        runner = CliRunner()
        mock_resolve.return_value = "123"
        mock_get_agent.return_value = {"agent_name": "test-agent"}

        result = runner.invoke(app, ["delete", "--agent", "test-agent"], input="n\n")
        assert result.exit_code == 0
        assert "Aborted" in result.stdout


class TestAgentDownload:
    """Test cases for agent download command."""

    @patch("konic.cli.src.agents.get_agent_by_id")
    @patch("konic.cli.src.agents.client")
    @patch("zipfile.ZipFile")
    def test_download_agent_success(self, mock_zipfile, mock_client, mock_get_agent):
        """Test successful agent download."""
        runner = CliRunner()
        mock_get_agent.return_value = {"agent_name": "test-agent", "agent_version": "v1"}
        mock_client.download_file.return_value = Path("/tmp/test-agent-v1.zip")

        with runner.isolated_filesystem():
            result = runner.invoke(app, ["download", "123"])
            assert result.exit_code == 0

    @patch("konic.cli.src.agents.get_agent_by_id")
    @patch("konic.cli.src.agents.client")
    @patch("zipfile.ZipFile")
    def test_download_agent_with_version(self, mock_zipfile, mock_client, mock_get_agent):
        """Test agent download with specific version."""
        runner = CliRunner()
        mock_get_agent.return_value = {"agent_name": "test-agent", "agent_version": "v1"}
        mock_client.download_file.return_value = Path("/tmp/test-agent-v1.zip")

        with runner.isolated_filesystem():
            result = runner.invoke(app, ["download", "123", "--version", "v1"])
            assert result.exit_code == 0

    @patch("konic.cli.src.agents.get_agent_by_id")
    @patch("konic.cli.src.agents.client")
    @patch("zipfile.ZipFile")
    def test_download_agent_keep_zip(self, mock_zipfile, mock_client, mock_get_agent):
        """Test agent download with keep-zip flag."""
        runner = CliRunner()
        mock_get_agent.return_value = {"agent_name": "test-agent", "agent_version": "v1"}
        mock_zip_path = MagicMock(spec=Path)
        mock_zip_path.exists.return_value = True
        mock_client.download_file.return_value = mock_zip_path

        with runner.isolated_filesystem():
            result = runner.invoke(app, ["download", "123", "--keep-zip"])
            assert result.exit_code == 0

    @patch("konic.cli.src.agents.zipfile.ZipFile")
    @patch("konic.cli.src.agents.get_agent_by_id")
    @patch("konic.cli.src.agents.client")
    def test_download_agent_path_traversal_protection(
        self, mock_client, mock_get_agent, mock_zipfile
    ):
        """Test that agent downloads are protected against path traversal attacks.

        This test verifies that malicious agent names with path traversal
        sequences (e.g., ../../../etc/passwd) are sanitized before being
        used in file paths, preventing directory escape.
        """
        runner = CliRunner()
        # Simulate a malicious agent with path traversal in the name
        mock_get_agent.return_value = {"agent_name": "../../../etc/passwd", "agent_version": "v1"}

        # Create a mock zip file
        mock_zip_path = MagicMock(spec=Path)
        mock_zip_path.exists.return_value = True
        mock_client.download_file.return_value = mock_zip_path

        # Mock the zipfile context manager
        mock_zip_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        with runner.isolated_filesystem():
            cwd = Path.cwd()
            result = runner.invoke(app, ["download", "123"])

            # The command should succeed by sanitizing the path
            assert result.exit_code == 0

            # Verify that the extractall was called with a sanitized path
            extract_call = mock_zip_instance.extractall.call_args
            assert extract_call is not None
            extract_path = extract_call[0][0]

            # The path should be sanitized - no ".." or "/" in the directory name
            assert ".." not in str(extract_path)
            assert "/" not in extract_path.name  # Only check the directory name part

            # Verify the path starts with expected sanitized name
            # "../../../etc/passwd" should become "_etc_passwd" or similar
            assert "etc" in str(extract_path) or "_" in str(extract_path)

            # Most importantly: verify it's still under our working directory
            # A relative path without ".." is safe - when resolved, it stays in cwd
            resolved_path = (cwd / extract_path).resolve()
            assert resolved_path.is_relative_to(cwd)

    @patch("konic.cli.src.agents.zipfile.ZipFile")
    @patch("konic.cli.src.agents.get_agent_by_id")
    @patch("konic.cli.src.agents.client")
    def test_download_agent_sanitizes_various_attacks(
        self, mock_client, mock_get_agent, mock_zipfile
    ):
        """Test that various path traversal attack vectors are sanitized.

        Tests multiple attack patterns including Windows paths, absolute paths,
        and hidden files.
        """
        runner = CliRunner()

        attack_names = [
            ("..\\..\\windows\\system32", "Windows-style path traversal"),
            ("/etc/passwd", "Absolute Unix path"),
            ("../../../secret", "Unix path traversal"),
            ("....//....//etc", "Double-dot slash attack"),
            (".hidden_malware", "Hidden file attempt"),
        ]

        for attack_name, description in attack_names:
            mock_get_agent.return_value = {"agent_name": attack_name, "agent_version": "v1"}

            mock_zip_path = MagicMock(spec=Path)
            mock_zip_path.exists.return_value = True
            mock_client.download_file.return_value = mock_zip_path

            mock_zip_instance = MagicMock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

            with runner.isolated_filesystem():
                cwd = Path.cwd()
                result = runner.invoke(app, ["download", "123"])

                # Should succeed with sanitization
                assert result.exit_code == 0, f"Failed for {description}: {attack_name}"

                # Verify extraction path is safe
                extract_call = mock_zip_instance.extractall.call_args
                if extract_call:
                    extract_path = extract_call[0][0]
                    # Should not contain dangerous patterns
                    path_str = str(extract_path)
                    assert ".." not in path_str, f"Contains '..' for {description}"
                    # Should be relative to cwd
                    assert not extract_path.is_absolute() or extract_path.is_relative_to(
                        cwd
                    ), f"Path escapes cwd for {description}"

            # Reset mocks for next iteration
            mock_zip_instance.reset_mock()
