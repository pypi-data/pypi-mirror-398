import inspect
from collections.abc import Callable

from konic.environment.reward.enums import KonicRewardKeys


def get_custom_reward_fns(obj) -> list[Callable[..., float]]:
    """Retrieve a list of custom reward functions from the given object using introspection."""
    members = inspect.getmembers(obj, predicate=inspect.ismethod)
    return [fn for _, fn in members if hasattr(fn, KonicRewardKeys.CUSTOM_REWARD_FN_ATTR_KEY.value)]
