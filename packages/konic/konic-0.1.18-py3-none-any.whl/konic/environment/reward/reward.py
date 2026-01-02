from __future__ import annotations

from typing import TYPE_CHECKING

from konic.common.errors import KonicError
from konic.environment.reward.base import BaseKonicRewardComposer
from konic.environment.reward.reducers.base import BaseKonicRewardReducer
from konic.environment.reward.reducers.strategy import SumReducerStrategy
from konic.environment.reward.utils import get_custom_reward_fns

if TYPE_CHECKING:
    from konic.environment import KonicEnvironment


class KonicRewardComposer[TKonicEnvironment: "KonicEnvironment"](BaseKonicRewardComposer):
    """Concrete implementation of the reward composer that uses a reducer strategy."""

    env: TKonicEnvironment
    reducer: type[BaseKonicRewardReducer] = SumReducerStrategy

    def set_env(self, env: TKonicEnvironment):
        """
        Bind the environment instance to this reward composer.

        This method is typically called by KonicEnvironment during initialization
        to provide the reward composer with a reference to the environment instance
        for use in custom reward functions.

        Args:
            env: The environment instance to bind.
        """
        self.env = env

    def compose(self) -> float:
        """Compose the total reward using custom functions and reducer."""
        reducer = self.reducer()
        fns = get_custom_reward_fns(self)

        if any(fns):
            try:
                return reducer.reduce(fns)
            except Exception as e:
                raise KonicError(f"Error in custom reward function: {e}") from e

        return self.reward()

    def reward(self) -> float:
        """Compute the base reward value."""
        raise KonicError(f"{self.__class__.__name__}.reward() is not implemented")
