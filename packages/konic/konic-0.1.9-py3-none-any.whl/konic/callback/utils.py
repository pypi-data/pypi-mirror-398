from collections.abc import Callable
from typing import Any

from konic.callback.enums import KonicCallbackKeys


def get_custom_metric_fns(instance: Any) -> list[Callable[..., dict[str, float]]]:
    """
    Get all custom metric functions from a callback instance.

    Scans the instance for methods decorated with @custom_metric and returns them.

    Args:
        instance: A KonicRLCallback instance to scan for custom metrics.

    Returns:
        A list of callable custom metric functions.
    """
    fns = []
    for attr_name in dir(instance):
        if attr_name.startswith("_"):
            continue
        attr = getattr(instance, attr_name, None)
        if callable(attr) and hasattr(attr, KonicCallbackKeys.CUSTOM_METRIC_FN_ATTR_KEY.value):
            fns.append(attr)
    return fns
