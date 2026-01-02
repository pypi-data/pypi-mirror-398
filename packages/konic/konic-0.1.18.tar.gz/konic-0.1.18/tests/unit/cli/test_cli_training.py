"""Unit tests for training CLI commands."""

from unittest.mock import patch

from typer.testing import CliRunner

from konic.cli.src.training import app
from konic.common.errors import KonicHTTPError


class TestTrainingStart:
    """Test cases for training start command."""

    @patch("konic.cli.src.training.resolve_agent_identifier")
    @patch("konic.cli.src.training.client")
    def test_start_training_success(self, mock_client, mock_resolve):
        """Test successful training start."""
        runner = CliRunner()
        mock_resolve.return_value = "123"
        mock_client.post_json.return_value = {
            "id": "job-123",
            "agent_name": "test-agent",
            "agent_version": "v1",
            "agent_id": "123",
            "status": "pending",
            "iterations": 100,
            "current_iteration": 0,
            "created_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["start", "test-agent", "--iterations", "100"])
        assert result.exit_code == 0
        assert "started successfully" in result.stdout.lower()

    @patch("konic.cli.src.training.resolve_agent_identifier")
    @patch("konic.cli.src.training.client")
    def test_start_training_with_checkpoint_interval(self, mock_client, mock_resolve):
        """Test training start with checkpoint interval."""
        runner = CliRunner()
        mock_resolve.return_value = "123"
        mock_client.post_json.return_value = {
            "id": "job-123",
            "agent_name": "test-agent",
            "status": "pending",
            "iterations": 100,
            "current_iteration": 0,
            "created_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(
            app, ["start", "test-agent", "--iterations", "100", "--checkpoint-interval", "25"]
        )
        assert result.exit_code == 0
        assert "Checkpoint interval" in result.stdout

    @patch("konic.cli.src.training.resolve_agent_identifier")
    @patch("konic.cli.src.training.client")
    @patch("konic.cli.src.training._watch_training")
    def test_start_training_with_watch(self, mock_watch, mock_client, mock_resolve):
        """Test training start with watch flag."""
        runner = CliRunner()
        mock_resolve.return_value = "123"
        mock_client.post_json.return_value = {
            "id": "job-123",
            "agent_name": "test-agent",
            "status": "pending",
            "iterations": 100,
            "current_iteration": 0,
            "created_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["start", "test-agent", "--iterations", "100", "--watch"])
        assert result.exit_code == 0
        mock_watch.assert_called_once()


class TestTrainingStatus:
    """Test cases for training status command."""

    @patch("konic.cli.src.training.client")
    def test_get_status_success(self, mock_client):
        """Test successful status retrieval."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "id": "job-123",
            "agent_name": "test-agent",
            "status": "running",
            "iterations": 100,
            "current_iteration": 50,
            "created_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["status", "job-123"])
        assert result.exit_code == 0
        assert "test-agent" in result.stdout

    @patch("konic.cli.src.training.client")
    def test_get_status_not_found(self, mock_client):
        """Test status retrieval for non-existent job."""
        runner = CliRunner()
        mock_client.get_json.side_effect = KonicHTTPError(
            status_code=404, message="Not Found", endpoint="/training/jobs/job-123"
        )

        result = runner.invoke(app, ["status", "job-123"])
        assert result.exit_code == 1


class TestTrainingList:
    """Test cases for training list command."""

    @patch("konic.cli.src.training.resolve_agent_identifier")
    @patch("konic.cli.src.training.client")
    def test_list_jobs_success(self, mock_client, mock_resolve):
        """Test successful job listing."""
        runner = CliRunner()
        mock_resolve.return_value = "123"
        mock_client.get_json.return_value = [
            {
                "id": "job-123",
                "agent_name": "test-agent",
                "status": "completed",
                "iterations": 100,
                "current_iteration": 100,
                "created_at": "2024-01-01T00:00:00",
            }
        ]

        result = runner.invoke(app, ["list", "test-agent"])
        assert result.exit_code == 0
        assert "job-123" in result.stdout

    @patch("konic.cli.src.training.resolve_agent_identifier")
    @patch("konic.cli.src.training.client")
    def test_list_jobs_empty(self, mock_client, mock_resolve):
        """Test job listing with no jobs."""
        runner = CliRunner()
        mock_resolve.return_value = "123"
        mock_client.get_json.return_value = []

        result = runner.invoke(app, ["list", "test-agent"])
        assert result.exit_code == 0
        assert "No training jobs found" in result.stdout

    @patch("konic.cli.src.training.resolve_agent_identifier")
    @patch("konic.cli.src.training.client")
    def test_list_jobs_with_status_filter(self, mock_client, mock_resolve):
        """Test job listing with status filter."""
        runner = CliRunner()
        mock_resolve.return_value = "123"
        mock_client.get_json.return_value = []

        result = runner.invoke(app, ["list", "test-agent", "--status", "completed"])
        assert result.exit_code == 0


class TestTrainingLogs:
    """Test cases for training logs command."""

    @patch("konic.cli.src.training.client")
    def test_get_logs_success(self, mock_client):
        """Test successful logs retrieval."""
        runner = CliRunner()
        mock_client.get_json.return_value = {"logs": "Training iteration 1\nTraining iteration 2\n"}

        result = runner.invoke(app, ["logs", "job-123"])
        assert result.exit_code == 0
        assert "Training iteration" in result.stdout

    @patch("konic.cli.src.training.client")
    def test_get_logs_with_tail(self, mock_client):
        """Test logs retrieval with tail option."""
        runner = CliRunner()
        mock_client.get_json.return_value = {"logs": "Training iteration 1\n"}

        result = runner.invoke(app, ["logs", "job-123", "--tail", "10"])
        assert result.exit_code == 0

    @patch("konic.cli.src.training.client")
    def test_get_logs_empty(self, mock_client):
        """Test logs retrieval with no logs."""
        runner = CliRunner()
        mock_client.get_json.return_value = {"logs": ""}

        result = runner.invoke(app, ["logs", "job-123"])
        assert result.exit_code == 0
        assert "No logs available" in result.stdout

    @patch("konic.cli.src.training.client")
    def test_get_logs_not_found(self, mock_client):
        """Test logs retrieval for non-existent job."""
        runner = CliRunner()
        mock_client.get_json.side_effect = KonicHTTPError(
            status_code=404, message="Not Found", endpoint="/training/jobs/job-123/logs"
        )

        result = runner.invoke(app, ["logs", "job-123"])
        assert result.exit_code == 1


class TestTrainingCancel:
    """Test cases for training cancel command."""

    @patch("konic.cli.src.training.client")
    def test_cancel_job_with_force(self, mock_client):
        """Test job cancellation with force flag."""
        runner = CliRunner()
        mock_client.post_json.return_value = {
            "id": "job-123",
            "status": "cancelled",
            "created_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["cancel", "job-123", "--force"])
        assert result.exit_code == 0
        assert "cancelled successfully" in result.stdout.lower()

    @patch("konic.cli.src.training.client")
    def test_cancel_job_with_confirmation(self, mock_client):
        """Test job cancellation with confirmation."""
        runner = CliRunner()
        mock_client.post_json.return_value = {
            "id": "job-123",
            "status": "cancelled",
            "created_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["cancel", "job-123"], input="y\n")
        assert result.exit_code == 0

    @patch("konic.cli.src.training.client")
    def test_cancel_job_declined(self, mock_client):
        """Test job cancellation declined by user.

        Note: User declining is a normal exit (code 0), not an error (code 1).
        """
        runner = CliRunner()

        result = runner.invoke(app, ["cancel", "job-123"], input="n\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.stdout

    @patch("konic.cli.src.training.client")
    def test_cancel_job_not_found(self, mock_client):
        """Test cancellation of non-existent job."""
        runner = CliRunner()
        mock_client.post_json.side_effect = KonicHTTPError(
            status_code=404, message="Not Found", endpoint="/training/jobs/job-123/cancel"
        )

        result = runner.invoke(app, ["cancel", "job-123", "--force"])
        assert result.exit_code == 1


class TestTrainingDelete:
    """Test cases for training delete command."""

    @patch("konic.cli.src.training.client")
    def test_delete_job_with_force(self, mock_client):
        """Test job deletion with force flag."""
        runner = CliRunner()

        result = runner.invoke(app, ["delete", "job-123", "--force"])
        assert result.exit_code == 0
        mock_client.delete.assert_called_once()

    @patch("konic.cli.src.training.client")
    def test_delete_job_with_confirmation(self, mock_client):
        """Test job deletion with confirmation."""
        runner = CliRunner()

        result = runner.invoke(app, ["delete", "job-123"], input="y\n")
        assert result.exit_code == 0
        mock_client.delete.assert_called_once()

    @patch("konic.cli.src.training.client")
    def test_delete_job_declined(self, mock_client):
        """Test job deletion declined by user.

        Note: User declining is a normal exit (code 0), not an error (code 1).
        """
        runner = CliRunner()

        result = runner.invoke(app, ["delete", "job-123"], input="n\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.stdout


class TestTrainingMetrics:
    """Test cases for training metrics command."""

    @patch("konic.cli.src.training.client")
    def test_get_metrics_success(self, mock_client):
        """Test successful metrics retrieval."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "iterations": [1, 2, 3],
            "episode_return_mean": [10.5, 12.3, 15.0],
            "episode_length_mean": [100, 110, 105],
            "fps": [500, 520, 510],
        }

        result = runner.invoke(app, ["metrics", "job-123"])
        assert result.exit_code == 0

    @patch("konic.cli.src.training.client")
    def test_get_metrics_json_output(self, mock_client):
        """Test metrics retrieval with JSON output."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "iterations": [1, 2],
            "episode_return_mean": [10.5, 12.3],
        }

        result = runner.invoke(app, ["metrics", "job-123", "--json"])
        assert result.exit_code == 0

    @patch("konic.cli.src.training.client")
    def test_get_metrics_empty(self, mock_client):
        """Test metrics retrieval with no metrics."""
        runner = CliRunner()
        mock_client.get_json.return_value = {"iterations": []}

        result = runner.invoke(app, ["metrics", "job-123"])
        assert result.exit_code == 0
        assert "No metrics available" in result.stdout


class TestTrainingWatch:
    """Test cases for training watch command."""

    @patch("konic.cli.src.training._watch_training")
    @patch("konic.cli.src.training.client")
    def test_watch_job_running(self, mock_client, mock_watch):
        """Test watching a running job."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "id": "job-123",
            "status": "running",
            "iterations": 100,
            "current_iteration": 50,
        }

        result = runner.invoke(app, ["watch", "job-123"])
        assert result.exit_code == 0
        mock_watch.assert_called_once()

    @patch("konic.cli.src.training.client")
    def test_watch_job_completed(self, mock_client):
        """Test watching a completed job."""
        runner = CliRunner()
        mock_client.get_json.return_value = {
            "id": "job-123",
            "status": "completed",
            "iterations": 100,
            "current_iteration": 100,
            "created_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["watch", "job-123"])
        assert result.exit_code == 0
        assert "already completed" in result.stdout.lower()

    @patch("konic.cli.src.training.client")
    def test_watch_job_not_found(self, mock_client):
        """Test watching non-existent job."""
        runner = CliRunner()
        mock_client.get_json.side_effect = KonicHTTPError(
            status_code=404, message="Not Found", endpoint="/training/jobs/job-123"
        )

        result = runner.invoke(app, ["watch", "job-123"])
        assert result.exit_code == 1
