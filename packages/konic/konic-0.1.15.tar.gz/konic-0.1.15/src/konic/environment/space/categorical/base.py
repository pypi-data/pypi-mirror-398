from abc import ABC, abstractmethod

import gymnasium as gym
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefinedType


class BaseKonicSpaceTypeStrategy(ABC):
    @classmethod
    @abstractmethod
    def apply(cls, name: str, field: FieldInfo) -> dict[str, gym.spaces.Space]:
        pass

    @staticmethod
    def _has_default(field: FieldInfo) -> bool:
        """Check if the field has a default value set."""
        return not isinstance(field.default, PydanticUndefinedType)
