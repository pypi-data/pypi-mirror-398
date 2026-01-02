"""Unit tests for model CLI commands."""

from unittest.mock import patch

from typer.testing import CliRunner

from konic.cli.src.models import app
from konic.common.errors import (
    KonicHTTPError,
    KonicModelNotFoundError,
)


class TestModelList:
    """Test cases for model list command."""

    @patch("konic.cli.src.models.client")
    def test_list_models_success(self, mock_client):
        """Test successful model listing."""
        runner = CliRunner()
        mock_client.get_json.return_value = [
            {
                "display_name": "GPT-2",
                "hf_model_id": "gpt2",
                "id": "model-123",
                "task_type": "text-generation",
                "status": "ready",
                "file_size": 548000000,
                "updated_at": "2024-01-01T00:00:00",
            }
        ]

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "GPT-2" in result.stdout

    @patch("konic.cli.src.models.client")
    def test_list_models_empty(self, mock_client):
        """Test model listing with no models."""
        runner = CliRunner()
        mock_client.get_json.return_value = []

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No models found" in result.stdout

    @patch("konic.cli.src.models.client")
    def test_list_models_with_status_filter(self, mock_client):
        """Test model listing with status filter."""
        runner = CliRunner()
        mock_client.get_json.return_value = [
            {
                "display_name": "GPT-2",
                "hf_model_id": "gpt2",
                "status": "ready",
                "file_size": 548000000,
                "updated_at": "2024-01-01T00:00:00",
            }
        ]

        result = runner.invoke(app, ["list", "--status", "ready"])
        assert result.exit_code == 0

    @patch("konic.cli.src.models.client")
    def test_list_models_with_task_type_filter(self, mock_client):
        """Test model listing with task type filter."""
        runner = CliRunner()
        mock_client.get_json.return_value = []

        result = runner.invoke(app, ["list", "--task-type", "text-generation"])
        assert result.exit_code == 0

    @patch("konic.cli.src.models.client")
    def test_list_models_with_pagination(self, mock_client):
        """Test model listing with pagination."""
        runner = CliRunner()
        mock_client.get_json.return_value = []

        result = runner.invoke(app, ["list", "--start", "10", "--end", "30"])
        assert result.exit_code == 0

    @patch("konic.cli.src.models.client")
    def test_list_models_json_output(self, mock_client):
        """Test model listing with JSON output."""
        runner = CliRunner()
        mock_client.get_json.return_value = [{"display_name": "GPT-2", "hf_model_id": "gpt2"}]

        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0


class TestModelDownload:
    """Test cases for model download command."""

    @patch("konic.cli.src.models.client")
    def test_download_model_success(self, mock_client):
        """Test successful model download."""
        runner = CliRunner()
        mock_client.post_json.return_value = {
            "display_name": "GPT-2",
            "hf_model_id": "gpt2",
            "id": "model-123",
            "status": "downloading",
            "created_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["download", "gpt2"])
        assert result.exit_code == 0
        assert "downloading started" in result.stdout.lower()

    @patch("konic.cli.src.models.client")
    def test_download_model_not_found_on_hf(self, mock_client):
        """Test model download when model not found on HuggingFace."""
        runner = CliRunner()
        mock_client.post_json.side_effect = KonicHTTPError(
            status_code=404, message="Not Found", endpoint="/models/download"
        )

        result = runner.invoke(app, ["download", "nonexistent-model"])
        assert result.exit_code == 1

    @patch("konic.cli.src.models.client")
    def test_download_model_gated(self, mock_client):
        """Test model download when model is gated."""
        runner = CliRunner()
        mock_client.post_json.side_effect = KonicHTTPError(
            status_code=403, message="Forbidden", endpoint="/models/download"
        )

        result = runner.invoke(app, ["download", "meta-llama/Llama-2-7b"])
        assert result.exit_code == 1

    @patch("konic.cli.src.models.client")
    def test_download_model_conflict(self, mock_client):
        """Test model download when model already exists."""
        runner = CliRunner()
        mock_client.post_json.side_effect = KonicHTTPError(
            status_code=409, message="Conflict", endpoint="/models/download"
        )

        result = runner.invoke(app, ["download", "gpt2"])
        assert result.exit_code == 1

    @patch("konic.cli.src.models.client")
    def test_download_model_with_host_override(self, mock_client):
        """Test model download with host override."""
        runner = CliRunner()
        mock_client.post_json.return_value = {
            "display_name": "GPT-2",
            "hf_model_id": "gpt2",
            "status": "downloading",
        }

        result = runner.invoke(app, ["download", "gpt2", "--host", "https://custom.api.com"])
        assert result.exit_code == 0
        mock_client.set_base_url.assert_called_with("https://custom.api.com")


class TestModelDetails:
    """Test cases for model details command."""

    @patch("konic.cli.src.models._resolve_model_by_hf_id")
    def test_model_details_success(self, mock_resolve):
        """Test successful model details retrieval."""
        runner = CliRunner()
        mock_resolve.return_value = {
            "display_name": "GPT-2",
            "hf_model_id": "gpt2",
            "id": "model-123",
            "task_type": "text-generation",
            "architecture": "gpt2",
            "license": "mit",
            "tags": ["conversational", "text-generation"],
            "file_size": 548000000,
            "local_path": "/models/gpt2",
            "status": "ready",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        result = runner.invoke(app, ["details", "gpt2"])
        assert result.exit_code == 0
        assert "GPT-2" in result.stdout

    @patch("konic.cli.src.models._resolve_model_by_hf_id")
    def test_model_details_not_found(self, mock_resolve):
        """Test model details when model not found."""
        runner = CliRunner()
        mock_resolve.side_effect = KonicModelNotFoundError("nonexistent-model", context="registry")

        result = runner.invoke(app, ["details", "nonexistent-model"])
        assert result.exit_code == 1

    @patch("konic.cli.src.models._resolve_model_by_hf_id")
    def test_model_details_json_output(self, mock_resolve):
        """Test model details with JSON output."""
        runner = CliRunner()
        mock_resolve.return_value = {
            "display_name": "GPT-2",
            "hf_model_id": "gpt2",
            "status": "ready",
        }

        result = runner.invoke(app, ["details", "gpt2", "--json"])
        assert result.exit_code == 0


class TestModelDelete:
    """Test cases for model delete command."""

    @patch("konic.cli.src.models._resolve_model_by_hf_id")
    @patch("konic.cli.src.models.client")
    def test_delete_model_with_force(self, mock_client, mock_resolve):
        """Test model delete with force flag."""
        runner = CliRunner()
        mock_resolve.return_value = {
            "id": "model-123",
            "display_name": "GPT-2",
            "hf_model_id": "gpt2",
        }

        result = runner.invoke(app, ["delete", "gpt2", "--force"])
        assert result.exit_code == 0
        mock_client.delete.assert_called_once_with("/models/model-123")

    @patch("konic.cli.src.models._resolve_model_by_hf_id")
    @patch("konic.cli.src.models.client")
    def test_delete_model_with_confirmation(self, mock_client, mock_resolve):
        """Test model delete with confirmation."""
        runner = CliRunner()
        mock_resolve.return_value = {
            "id": "model-123",
            "display_name": "GPT-2",
            "hf_model_id": "gpt2",
        }

        result = runner.invoke(app, ["delete", "gpt2"], input="y\n")
        assert result.exit_code == 0
        mock_client.delete.assert_called_once()

    @patch("konic.cli.src.models._resolve_model_by_hf_id")
    def test_delete_model_cancelled(self, mock_resolve):
        """Test model delete cancelled by user."""
        runner = CliRunner()
        mock_resolve.return_value = {
            "id": "model-123",
            "display_name": "GPT-2",
            "hf_model_id": "gpt2",
        }

        result = runner.invoke(app, ["delete", "gpt2"], input="n\n")
        assert result.exit_code == 0
        assert "Aborted" in result.stdout

    @patch("konic.cli.src.models._resolve_model_by_hf_id")
    def test_delete_model_not_found(self, mock_resolve):
        """Test model delete when model not found."""
        runner = CliRunner()
        mock_resolve.side_effect = KonicModelNotFoundError("nonexistent-model", context="registry")

        result = runner.invoke(app, ["delete", "nonexistent-model", "--force"])
        assert result.exit_code == 1

    @patch("konic.cli.src.models._resolve_model_by_hf_id")
    @patch("konic.cli.src.models.client")
    def test_delete_model_http_error(self, mock_client, mock_resolve):
        """Test model delete with HTTP error."""
        runner = CliRunner()
        mock_resolve.return_value = {
            "id": "model-123",
            "display_name": "GPT-2",
            "hf_model_id": "gpt2",
        }
        mock_client.delete.side_effect = KonicHTTPError(
            status_code=404, message="Not Found", endpoint="/models/model-123"
        )

        result = runner.invoke(app, ["delete", "gpt2", "--force"])
        assert result.exit_code == 1


class TestModelTaskTypes:
    """Test cases for model task-types command."""

    @patch("konic.cli.src.models.client")
    def test_list_task_types_success(self, mock_client):
        """Test successful task types listing."""
        runner = CliRunner()
        mock_client.get_json.return_value = [
            "text-generation",
            "text-classification",
            "question-answering",
        ]

        result = runner.invoke(app, ["task-types"])
        assert result.exit_code == 0
        assert "text-generation" in result.stdout

    @patch("konic.cli.src.models.client")
    def test_list_task_types_empty(self, mock_client):
        """Test task types listing with no task types."""
        runner = CliRunner()
        mock_client.get_json.return_value = []

        result = runner.invoke(app, ["task-types"])
        assert result.exit_code == 0
        assert "No task types found" in result.stdout

    @patch("konic.cli.src.models.client")
    def test_list_task_types_json_output(self, mock_client):
        """Test task types listing with JSON output."""
        runner = CliRunner()
        mock_client.get_json.return_value = ["text-generation", "text-classification"]

        result = runner.invoke(app, ["task-types", "--json"])
        assert result.exit_code == 0

    @patch("konic.cli.src.models.client")
    def test_list_task_types_with_host_override(self, mock_client):
        """Test task types listing with host override."""
        runner = CliRunner()
        mock_client.get_json.return_value = ["text-generation"]

        result = runner.invoke(app, ["task-types", "--host", "https://custom.api.com"])
        assert result.exit_code == 0
        mock_client.set_base_url.assert_called_with("https://custom.api.com")
