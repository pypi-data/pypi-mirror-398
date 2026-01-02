import gymnasium as gym
import numpy as np
from pydantic.fields import FieldInfo

from konic.common.errors import KonicAssertionError
from konic.environment.space.categorical.base import BaseKonicSpaceTypeStrategy


class BoxSpaceStrategy(BaseKonicSpaceTypeStrategy):
    @classmethod
    def apply(cls, name: str, field: FieldInfo):
        shape, low, high = ((1,), -1, 1)

        if cls._has_default(field):
            if not (
                isinstance(field.default, tuple | list)
                and len(field.default) == 3
                and isinstance(field.default[0], tuple)
            ):
                raise KonicAssertionError("KonicBound type is not in a correct form")
            shape, low, high = field.default

        return {name: gym.spaces.Box(low, high, shape, dtype=np.float32)}


class DiscreteSpaceStrategy(BaseKonicSpaceTypeStrategy):
    @classmethod
    def apply(cls, name: str, field: FieldInfo):
        _default = 2

        if cls._has_default(field):
            if not (isinstance(field.default, int) and field.default > 1):
                raise KonicAssertionError("KonicDiscrete type is not in a correct form")
            _default = field.default

        return {name: gym.spaces.Discrete(_default)}


class MultiDiscreteSpaceStrategy(BaseKonicSpaceTypeStrategy):
    @classmethod
    def apply(cls, name: str, field: FieldInfo):
        _default = [2, 2]

        if cls._has_default(field):
            if not (
                isinstance(field.default, list) and all(list(map(lambda x: x > 1, field.default)))
            ):
                raise KonicAssertionError("KonicMultiDiscrete type is not in a correct form")
            _default = field.default

        return {name: gym.spaces.MultiDiscrete(_default)}
