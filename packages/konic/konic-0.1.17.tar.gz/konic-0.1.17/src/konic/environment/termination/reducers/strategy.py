from collections.abc import Callable

from konic.environment.termination.reducers.base import BaseKonicTerminationReducer


class OrReducerStrategy(BaseKonicTerminationReducer):
    """Termination reducer strategy that returns True if any custom termination function returns True."""

    def reduce(self, fns: list[Callable[..., bool]]) -> bool:
        return any(fn() for fn in fns)
