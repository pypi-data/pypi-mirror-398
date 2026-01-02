import functools

from konic.environment.reward.enums import KonicRewardKeys


def custom_reward(func):
    """Decorator to tag custom reward functions on KonicRewardComposer."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    setattr(wrapper, KonicRewardKeys.CUSTOM_REWARD_FN_ATTR_KEY.value, True)
    return wrapper
