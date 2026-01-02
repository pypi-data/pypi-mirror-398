import gymnasium as gym
from gymnasium.spaces import Space

from konic.common.errors import KonicError
from konic.environment.space.base import BaseKonicSpace
from konic.environment.space.categorical.strategy import (
    BoxSpaceStrategy,
    DiscreteSpaceStrategy,
    MultiDiscreteSpaceStrategy,
)
from konic.environment.space.type import KonicBound, KonicDiscrete, KonicMultiDiscrete


class KonicSpace(BaseKonicSpace):
    """Concrete implementation of a Konic space for Gymnasium integration."""

    @classmethod
    def to_gym(cls) -> gym.spaces.Dict:
        """Convert the Konic space to a Gymnasium Dict space."""
        _fields = cls.model_fields.items()
        _dict: dict[str, Space] = {}

        for name, field in _fields:
            if field.annotation == KonicBound:
                _dict |= BoxSpaceStrategy.apply(name, field)

            elif field.annotation == KonicDiscrete:
                _dict |= DiscreteSpaceStrategy.apply(name, field)

            elif field.annotation == KonicMultiDiscrete:
                _dict |= MultiDiscreteSpaceStrategy.apply(name, field)

            else:
                raise KonicError(
                    f"Unsupported field type '{field.annotation}' for field '{name}'. "
                    f"Expected KonicBound or KonicDiscrete."
                )

        return gym.spaces.Dict(_dict)
