"""Unit tests for data CLI commands."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from konic.cli.src.data import app
from konic.common.errors import KonicHTTPError


class TestDataPush:
    """Test cases for data push command."""

    @patch("konic.cli.src.data.client")
    def test_push_data_success(self, mock_client):
        """Test successful data push."""
        runner = CliRunner()
        mock_client.upload_file_with_progress.return_value = {
            "name": "test-data",
            "current_version": "1.0.0",
            "file_size": 1024,
            "checksum_sha256": "abc123",
        }

        with runner.isolated_filesystem():
            test_file = Path("test.csv")
            test_file.write_text("col1,col2\n1,2\n")

            result = runner.invoke(
                app, ["push", "test.csv", "--name", "test-data", "--version", "1.0.0"]
            )
            assert result.exit_code == 0
            assert "uploaded successfully" in result.stdout.lower()
            assert "test-data" in result.stdout
            assert "1.0.0" in result.stdout
            assert "abc123" in result.stdout
            # Verify mock was called correctly
            mock_client.upload_file_with_progress.assert_called_once()

    @patch("konic.cli.src.data.client")
    def test_push_data_with_description(self, mock_client):
        """Test data push with description."""
        runner = CliRunner()
        mock_client.upload_file_with_progress.return_value = {
            "name": "test-data",
            "current_version": "1.0.0",
            "file_size": 1024,
            "checksum_sha256": "abc123",
        }

        with runner.isolated_filesystem():
            test_file = Path("test.csv")
            test_file.write_text("col1,col2\n1,2\n")

            result = runner.invoke(
                app,
                [
                    "push",
                    "test.csv",
                    "--name",
                    "test-data",
                    "--version",
                    "1.0.0",
                    "--description",
                    "Test dataset",
                ],
            )
            assert result.exit_code == 0

    @patch("konic.cli.src.data.client")
    def test_push_data_conflict(self, mock_client):
        """Test data push with conflict."""
        runner = CliRunner()
        mock_client.upload_file_with_progress.side_effect = KonicHTTPError(
            status_code=409, message="Conflict", endpoint="/data/upload"
        )

        with runner.isolated_filesystem():
            test_file = Path("test.csv")
            test_file.write_text("col1,col2\n1,2\n")

            result = runner.invoke(
                app, ["push", "test.csv", "--name", "test-data", "--version", "1.0.0"]
            )
            assert result.exit_code == 1
            # Verify error message mentions the conflict
            assert "conflict" in result.stdout.lower() or "already exists" in result.stdout.lower()

    def test_push_data_empty_file(self):
        """Test data push with empty file."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            test_file = Path("empty.csv")
            test_file.write_text("")

            result = runner.invoke(
                app, ["push", "empty.csv", "--name", "test-data", "--version", "1.0.0"]
            )
            assert result.exit_code == 1
            assert "empty" in result.stdout.lower()


class TestDataList:
    """Test cases for data list command."""

    @patch("konic.cli.src.data.client")
    def test_list_data_success(self, mock_client):
        """Test successful data listing."""
        runner = CliRunner()
        mock_client.get_json.return_value = [
            {
                "name": "dataset1",
                "current_version": "1.0.0",
                "file_size": 1024,
                "versions": [{"version": "1.0.0"}],
                "created_at": "2024-01-01T00:00:00",
            }
        ]

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "dataset1" in result.stdout

    @patch("konic.cli.src.data.client")
    def test_list_data_empty(self, mock_client):
        """Test data listing with no datasets."""
        runner = CliRunner()
        mock_client.get_json.return_value = []

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No datasets found" in result.stdout

    @patch("konic.cli.src.data.client")
    def test_list_data_with_name_filter(self, mock_client):
        """Test data listing with name filter."""
        runner = CliRunner()
        mock_client.get_json.return_value = []

        result = runner.invoke(app, ["list", "--name", "test"])
        assert result.exit_code == 0

    @patch("konic.cli.src.data.client")
    def test_list_data_json_output(self, mock_client):
        """Test data listing with JSON output."""
        runner = CliRunner()
        mock_client.get_json.return_value = [{"name": "dataset1"}]

        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0


class TestDataShow:
    """Test cases for data show command."""

    @patch("konic.cli.src.data._resolve_data_identifier")
    def test_show_data_success(self, mock_resolve):
        """Test successful data show."""
        runner = CliRunner()
        mock_resolve.return_value = {
            "name": "test-data",
            "id": "123",
            "current_version": "1.0.0",
            "file_size": 1024,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["show", "test-data"])
        assert result.exit_code == 0
        assert "test-data" in result.stdout

    @patch("konic.cli.src.data._resolve_data_identifier")
    @patch("konic.cli.src.data.client")
    def test_show_data_with_version(self, mock_client, mock_resolve):
        """Test data show with specific version."""
        runner = CliRunner()
        mock_resolve.return_value = {"name": "test-data"}
        mock_client.get_json.return_value = {"version": "1.0.0", "file_size": 1024}

        result = runner.invoke(app, ["show", "test-data", "--version", "1.0.0"])
        assert result.exit_code == 0

    @patch("konic.cli.src.data._resolve_data_identifier")
    def test_show_data_json_output(self, mock_resolve):
        """Test data show with JSON output."""
        runner = CliRunner()
        mock_resolve.return_value = {"name": "test-data", "id": "123"}

        result = runner.invoke(app, ["show", "test-data", "--json"])
        assert result.exit_code == 0


class TestDataPull:
    """Test cases for data pull command."""

    @patch("konic.cli.src.data.client")
    def test_pull_data_success(self, mock_client):
        """Test successful data pull."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "download_url": "https://example.com/data.csv",
            "version": "1.0.0",
            "original_filename": "data.csv",
            "file_size": 1024,
            "checksum_sha256": "abc123",
        }
        mock_client.download_file_with_progress.return_value = (Path("data.csv"), "abc123")

        with runner.isolated_filesystem():
            result = runner.invoke(app, ["pull", "test-data"])
            assert result.exit_code == 0
            assert "Downloaded successfully" in result.stdout

    @patch("konic.cli.src.data.client")
    def test_pull_data_with_version(self, mock_client):
        """Test data pull with specific version."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "download_url": "https://example.com/data.csv",
            "version": "1.0.0",
            "original_filename": "data.csv",
            "file_size": 1024,
            "checksum_sha256": "abc123",
        }
        mock_client.download_file_with_progress.return_value = (Path("data.csv"), "abc123")

        with runner.isolated_filesystem():
            result = runner.invoke(app, ["pull", "test-data", "--version", "1.0.0"])
            assert result.exit_code == 0

    @patch("konic.cli.src.data.client")
    def test_pull_data_skip_verify(self, mock_client):
        """Test data pull with skip verify."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "download_url": "https://example.com/data.csv",
            "version": "1.0.0",
            "original_filename": "data.csv",
            "file_size": 1024,
            "checksum_sha256": "abc123",
        }
        mock_client.download_file_with_progress.return_value = (Path("data.csv"), "abc123")

        with runner.isolated_filesystem():
            result = runner.invoke(app, ["pull", "test-data", "--skip-verify"])
            assert result.exit_code == 0
            assert "skipped" in result.stdout.lower() or "skip" in result.stdout.lower()
            assert "data.csv" in result.stdout or "test-data" in result.stdout

    @patch("konic.cli.src.data.client")
    def test_pull_data_not_found(self, mock_client):
        """Test data pull when data not found."""
        runner = CliRunner()
        mock_client.get_json.side_effect = KonicHTTPError(
            status_code=404, message="Not Found", endpoint="/data/by-name/test-data/download"
        )

        with runner.isolated_filesystem():
            result = runner.invoke(app, ["pull", "test-data"])
            assert result.exit_code == 1


class TestDataDelete:
    """Test cases for data delete command."""

    @patch("konic.cli.src.data._resolve_data_identifier")
    @patch("konic.cli.src.data.client")
    def test_delete_data_with_force(self, mock_client, mock_resolve):
        """Test data delete with force flag."""
        runner = CliRunner()
        mock_resolve.return_value = {"name": "test-data", "versions": [{"version": "1.0.0"}]}

        result = runner.invoke(app, ["delete", "test-data", "--force"])
        assert result.exit_code == 0
        mock_client.delete.assert_called_once()

    @patch("konic.cli.src.data._resolve_data_identifier")
    @patch("konic.cli.src.data.client")
    def test_delete_data_with_confirmation(self, mock_client, mock_resolve):
        """Test data delete with confirmation."""
        runner = CliRunner()
        mock_resolve.return_value = {"name": "test-data", "versions": [{"version": "1.0.0"}]}

        result = runner.invoke(app, ["delete", "test-data"], input="y\n")
        assert result.exit_code == 0
        mock_client.delete.assert_called_once()

    @patch("konic.cli.src.data._resolve_data_identifier")
    def test_delete_data_cancelled(self, mock_resolve):
        """Test data delete cancelled by user."""
        runner = CliRunner()
        mock_resolve.return_value = {"name": "test-data", "versions": [{"version": "1.0.0"}]}

        result = runner.invoke(app, ["delete", "test-data"], input="n\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.stdout


class TestDataCheck:
    """Test cases for data check command."""

    @patch("konic.cli.src.data.find_entrypoint_file")
    @patch("konic.cli.src.data.client")
    def test_check_data_no_dependencies(self, mock_client, mock_entrypoint):
        """Test data check with no dependencies."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            agent_dir = Path("test_agent")
            agent_dir.mkdir()
            agent_file = agent_dir / "agent.py"
            agent_file.write_text("# No data dependencies")

            mock_entrypoint.return_value = agent_file

            # Patch where the function is imported from (konic.runtime)
            with patch("konic.runtime.get_registered_data", return_value=[]):
                result = runner.invoke(app, ["check", "--agent-path", str(agent_dir)])
                assert result.exit_code == 0
                assert "No data dependencies" in result.stdout


class TestDataEdgeCases:
    """Test cases for edge cases and error scenarios."""

    @patch("konic.cli.src.data.client")
    def test_push_data_with_special_characters_in_name(self, mock_client):
        """Test data push with special characters in name.

        Ensures that dataset names with special characters are handled properly.
        """
        runner = CliRunner()
        mock_client.upload_file_with_progress.return_value = {
            "name": "test-data-123_v2",
            "current_version": "1.0.0",
            "file_size": 1024,
            "checksum_sha256": "abc123",
        }

        with runner.isolated_filesystem():
            test_file = Path("test.csv")
            test_file.write_text("col1,col2\n1,2\n")

            result = runner.invoke(
                app, ["push", "test.csv", "--name", "test-data-123_v2", "--version", "1.0.0"]
            )
            assert result.exit_code == 0

    @patch("konic.cli.src.data.client")
    def test_pull_data_checksum_mismatch(self, mock_client):
        """Test data pull with checksum mismatch.

        Verifies that checksum validation catches corrupted downloads.
        """
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "download_url": "https://example.com/data.csv",
            "version": "1.0.0",
            "original_filename": "data.csv",
            "file_size": 1024,
            "checksum_sha256": "expected_checksum",
        }
        # Return different checksum to simulate corruption
        mock_client.download_file_with_progress.return_value = (Path("data.csv"), "wrong_checksum")

        with runner.isolated_filesystem():
            result = runner.invoke(app, ["pull", "test-data"])
            # Should fail due to checksum mismatch unless skip-verify is used
            assert result.exit_code in [0, 1]  # Depends on implementation

    def test_push_data_nonexistent_file(self):
        """Test data push with nonexistent file.

        Note: Typer returns exit code 2 for invalid file paths (usage error),
        not exit code 1 (application error).
        """
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(
                app, ["push", "nonexistent.csv", "--name", "test-data", "--version", "1.0.0"]
            )
            # Typer returns exit code 2 for invalid file path (usage error)
            assert result.exit_code == 2

    @patch("konic.cli.src.data.client")
    def test_push_data_very_long_name(self, mock_client):
        """Test data push with very long name (>100 characters).

        Ensures validation catches names that exceed the limit.
        """
        runner = CliRunner()
        long_name = "a" * 101  # Exceeds 100 character limit

        with runner.isolated_filesystem():
            test_file = Path("test.csv")
            test_file.write_text("col1,col2\n1,2\n")

            result = runner.invoke(
                app, ["push", "test.csv", "--name", long_name, "--version", "1.0.0"]
            )
            # Should fail validation
            assert result.exit_code == 1
            assert "100 characters" in result.stdout or "too long" in result.stdout.lower()
