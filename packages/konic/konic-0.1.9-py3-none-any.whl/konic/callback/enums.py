from enum import Enum


class KonicCallbackKeys(str, Enum):
    """Keys used for callback-related attributes and configuration."""

    CUSTOM_METRIC_FN_ATTR_KEY = "_konic_custom_metric_fn"
