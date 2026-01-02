import functools

from konic.callback.enums import KonicCallbackKeys


def custom_metric(func):
    """
    Decorator to tag custom metric functions on KonicRLCallback.

    Custom metric functions should return a dict[str, float] mapping
    metric names to their values.

    Example:
        class MyCallback(KonicRLCallback):
            @custom_metric
            def track_position(self, episode) -> dict[str, float]:
                return {"agent_x": episode.custom_data.get("x", 0.0)}
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    setattr(wrapper, KonicCallbackKeys.CUSTOM_METRIC_FN_ATTR_KEY.value, True)
    return wrapper
