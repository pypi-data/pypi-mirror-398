import inspect
from collections.abc import Callable

from konic.environment.termination.enums import KonicTerminationKeys


def get_custom_termination_fns(obj) -> list[Callable[..., bool]]:
    """Retrieve a list of custom termination functions from the given object using introspection."""
    members = inspect.getmembers(obj, predicate=inspect.ismethod)
    return [
        fn
        for _, fn in members
        if hasattr(fn, KonicTerminationKeys.CUSTOM_TERMINATION_FN_ATTR_KEY.value)
    ]
