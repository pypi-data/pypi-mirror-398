from enum import Enum


class BoilerplateOptions(str, Enum):
    basic = "basic"
    custom = "custom"
    csv_streamer = "csv_streamer"
    callback = "callback"
    full = "full"
    finetuning_basic = "finetuning_basic"
    finetuning_advanced = "finetuning_advanced"


class TrainingStatus(str, Enum):
    """Training job status enum."""

    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SSEEventType(str, Enum):
    """Server-Sent Events event types for training streams."""

    STATUS = "status"
    METRICS = "metrics"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class InferenceServerStatus(str, Enum):
    """Inference server status enum."""

    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
