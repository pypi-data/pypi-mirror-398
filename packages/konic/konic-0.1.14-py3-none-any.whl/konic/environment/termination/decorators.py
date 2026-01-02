import functools

from konic.environment.termination.enums import KonicTerminationKeys


def custom_termination(func):
    """Decorator to tag custom termination functions on KonicTerminationComposer."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    setattr(wrapper, KonicTerminationKeys.CUSTOM_TERMINATION_FN_ATTR_KEY.value, True)
    return wrapper
