from collections.abc import Callable

from konic.environment.reward.reducers.base import BaseKonicRewardReducer


class SumReducerStrategy(BaseKonicRewardReducer):
    """Reward reducer strategy that sums the results of all custom reward functions."""

    def reduce(self, fns: list[Callable[..., float]]) -> float:
        return sum(fn() for fn in fns)
