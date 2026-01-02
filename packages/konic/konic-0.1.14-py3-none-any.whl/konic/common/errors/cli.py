"""CLI and API Client specific error classes for Konic."""

from konic.common.errors.base import KonicError

__all__ = [
    "KonicCLIError",
    "KonicConfigurationError",
    "KonicAPIClientError",
    "KonicHTTPError",
    "KonicValidationError",
    "KonicEnvironmentError",
    "KonicAgentNotFoundError",
    "KonicAgentConflictError",
    "KonicAgentResolutionError",
    "KonicTrainingJobNotFoundError",
    "KonicTrainingJobError",
    "KonicDataNotFoundError",
    "KonicDataConflictError",
    "KonicDataValidationError",
    "KonicArtifactNotFoundError",
    "KonicInferenceServerNotFoundError",
    "KonicModelNotFoundError",
    "KonicModelConflictError",
    "KonicModelGatedError",
]


class KonicCLIError(KonicError):
    """Base exception for CLI-related errors."""

    def __init__(self, message: str, exit_code: int = 1):
        """
        Initialize CLI error.

        Args:
            message: The error message
            exit_code: The exit code to use when this error occurs
        """
        super().__init__(message)
        self.exit_code = exit_code


class KonicConfigurationError(KonicCLIError):
    """Exception raised when there are configuration issues (missing env vars, invalid config, etc.)."""

    def __init__(self, message: str, config_key: str | None = None):
        """
        Initialize configuration error.

        Args:
            message: The error message
            config_key: The configuration key that caused the error
        """
        super().__init__(message, exit_code=1)
        self.config_key = config_key


class KonicEnvironmentError(KonicConfigurationError):
    """Exception raised when required environment variables are missing or invalid."""

    def __init__(self, env_var: str, suggestion: str | None = None):
        """
        Initialize environment error.

        Args:
            env_var: The environment variable that is missing or invalid
            suggestion: Optional suggestion on how to set the variable
        """
        message = f"Missing or invalid environment variable: {env_var}"
        if suggestion:
            message += f"\n💡 Suggestion: {suggestion}"
        super().__init__(message, config_key=env_var)
        self.env_var = env_var


class KonicAPIClientError(KonicCLIError):
    """Base exception for API client errors."""

    def __init__(self, message: str, endpoint: str | None = None):
        """
        Initialize API client error.

        Args:
            message: The error message
            endpoint: The API endpoint that caused the error
        """
        super().__init__(message, exit_code=1)
        self.endpoint = endpoint


class KonicHTTPError(KonicAPIClientError):
    """Exception raised when HTTP requests fail."""

    def __init__(
        self,
        message: str,
        status_code: int,
        endpoint: str | None = None,
        response_body: str | None = None,
    ):
        """
        Initialize HTTP error.

        Args:
            message: The error message
            status_code: HTTP status code
            endpoint: The API endpoint that caused the error
            response_body: Optional response body for debugging
        """
        super().__init__(message, endpoint=endpoint)
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        """Return formatted error message."""
        base = f"HTTP {self.status_code}"
        if self.endpoint:
            base += f" at {self.endpoint}"
        base += f": {self.message}"
        return base


class KonicValidationError(KonicCLIError):
    """Exception raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None):
        """
        Initialize validation error.

        Args:
            message: The error message
            field: The field that failed validation
        """
        super().__init__(message, exit_code=1)
        self.field = field


class KonicAgentNotFoundError(KonicAPIClientError):
    """Exception raised when an agent is not found (404)."""

    def __init__(self, agent_identifier: str):
        """
        Initialize agent not found error.

        Args:
            agent_identifier: The agent name or ID that was not found
        """
        message = f"Agent not found: {agent_identifier}"
        super().__init__(message, endpoint="/agents")
        self.agent_identifier = agent_identifier


class KonicAgentConflictError(KonicAPIClientError):
    """Exception raised when there's a conflict creating an agent (409), e.g., duplicate name."""

    def __init__(self, agent_name: str):
        """
        Initialize agent conflict error.

        Args:
            agent_name: The agent name that caused the conflict
        """
        message = f"Agent with name '{agent_name}' already exists. Use 'konic agent update' to add a new version."
        super().__init__(message, endpoint="/agents/upload")
        self.agent_name = agent_name


class KonicAgentResolutionError(KonicAPIClientError):
    """Exception raised when multiple agents match a given name."""

    def __init__(self, agent_name: str, count: int):
        """
        Initialize agent resolution error.

        Args:
            agent_name: The agent name that matched multiple agents
            count: The number of agents that matched
        """
        message = f"Multiple agents ({count}) found with name '{agent_name}'. Please use the agent ID instead."
        super().__init__(message, endpoint="/agents")
        self.agent_name = agent_name
        self.count = count


class KonicTrainingJobNotFoundError(KonicAPIClientError):
    """Exception raised when a training job is not found (404)."""

    def __init__(self, job_id: str):
        """
        Initialize training job not found error.

        Args:
            job_id: The training job ID that was not found
        """
        message = f"Training job not found: {job_id}"
        super().__init__(message, endpoint="/training/jobs")
        self.job_id = job_id


class KonicTrainingJobError(KonicAPIClientError):
    """Exception raised for training job operation errors."""

    def __init__(self, message: str, job_id: str | None = None):
        """
        Initialize training job error.

        Args:
            message: The error message
            job_id: The training job ID (optional)
        """
        super().__init__(message, endpoint="/training/jobs")
        self.job_id = job_id


class KonicDataNotFoundError(KonicAPIClientError):
    """Exception raised when a dataset is not found (404)."""

    def __init__(self, data_identifier: str):
        """
        Initialize data not found error.

        Args:
            data_identifier: The dataset name or ID that was not found
        """
        message = f"Dataset not found: {data_identifier}"
        super().__init__(message, endpoint="/data")
        self.data_identifier = data_identifier


class KonicDataConflictError(KonicAPIClientError):
    """Exception raised when there's a version conflict (409)."""

    def __init__(self, data_name: str, version: str):
        """
        Initialize data conflict error.

        Args:
            data_name: The dataset name
            version: The version that already exists
        """
        message = f"Version '{version}' already exists for dataset '{data_name}'."
        super().__init__(message, endpoint="/data/upload")
        self.data_name = data_name
        self.version = version


class KonicDataValidationError(KonicAPIClientError):
    """Exception raised when data validation fails."""

    def __init__(self, message: str, field: str | None = None):
        """
        Initialize data validation error.

        Args:
            message: The error message
            field: The field that failed validation (optional)
        """
        super().__init__(message, endpoint="/data")
        self.field = field


class KonicArtifactNotFoundError(KonicAPIClientError):
    """Exception raised when an artifact is not found (404)."""

    def __init__(self, artifact_id: str):
        """
        Initialize artifact not found error.

        Args:
            artifact_id: The artifact ID that was not found
        """
        message = f"Artifact not found: {artifact_id}"
        super().__init__(message, endpoint="/artifacts")
        self.artifact_id = artifact_id


class KonicInferenceServerNotFoundError(KonicAPIClientError):
    """Exception raised when an inference server is not found (404)."""

    def __init__(self, server_id: str):
        """
        Initialize inference server not found error.

        Args:
            server_id: The inference server ID that was not found
        """
        message = f"Inference server not found: {server_id}"
        super().__init__(message, endpoint="/inference")
        self.server_id = server_id


class KonicModelNotFoundError(KonicAPIClientError):
    """Exception raised when a HuggingFace model is not found (404)."""

    def __init__(self, hf_model_id: str, context: str = "registry"):
        """
        Initialize model not found error.

        Args:
            hf_model_id: The HuggingFace model ID that was not found
            context: Where the model was not found ("registry" or "huggingface")
        """
        if context == "huggingface":
            message = f"Model not found on HuggingFace Hub: {hf_model_id}"
        else:
            message = f"Model not found in registry: {hf_model_id}"
        super().__init__(message, endpoint="/models")
        self.hf_model_id = hf_model_id
        self.context = context


class KonicModelConflictError(KonicAPIClientError):
    """Exception raised when a model already exists in the registry (409)."""

    def __init__(self, hf_model_id: str):
        """
        Initialize model conflict error.

        Args:
            hf_model_id: The HuggingFace model ID that already exists
        """
        message = f"Model '{hf_model_id}' is already downloaded."
        super().__init__(message, endpoint="/models/download")
        self.hf_model_id = hf_model_id


class KonicModelGatedError(KonicAPIClientError):
    """Exception raised when trying to download a gated model (403)."""

    def __init__(self, hf_model_id: str):
        """
        Initialize model gated error.

        Args:
            hf_model_id: The HuggingFace model ID that is gated
        """
        message = f"Model '{hf_model_id}' is gated. Only public models are supported."
        super().__init__(message, endpoint="/models/download")
        self.hf_model_id = hf_model_id
