from __future__ import annotations

from typing import TYPE_CHECKING

from konic.common.errors import KonicError
from konic.environment.termination.base import BaseKonicTerminationComposer
from konic.environment.termination.reducers.base import BaseKonicTerminationReducer
from konic.environment.termination.reducers.strategy import OrReducerStrategy
from konic.environment.termination.utils import get_custom_termination_fns

if TYPE_CHECKING:
    from konic.environment import KonicEnvironment


class KonicTerminationComposer[TKonicEnvironment: "KonicEnvironment"](BaseKonicTerminationComposer):
    """Concrete implementation of the termination composer that uses a reducer strategy."""

    env: TKonicEnvironment
    reducer: type[BaseKonicTerminationReducer] = OrReducerStrategy

    def set_env(self, env: TKonicEnvironment):
        """
        Bind the environment instance to this termination composer.

        This method is typically called by KonicEnvironment during initialization
        to provide the termination composer with a reference to the environment instance
        for use in custom termination functions.

        Args:
            env: The environment instance to bind.
        """
        self.env = env

    def compose(self) -> bool:
        """Compose the termination decision using custom functions and reducer."""
        reducer = self.reducer()
        fns = get_custom_termination_fns(self)

        if any(fns):
            try:
                return reducer.reduce(fns)
            except Exception as e:
                raise KonicError(f"Error in custom termination function: {e}") from e

        return self.terminated()

    def terminated(self) -> bool:
        """Compute the base termination value."""
        raise KonicError(f"{self.__class__.__name__}.terminated() is not implemented")
