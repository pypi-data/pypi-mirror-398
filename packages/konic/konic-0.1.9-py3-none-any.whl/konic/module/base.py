from abc import ABC

from ray.rllib.core.rl_module.torch import TorchRLModule

from konic.module.type import KonicAlgorithmType


class BaseTorchModule(TorchRLModule, ABC):
    """Abstract base class of KonicTorchXXX class interface"""

    algorithm: KonicAlgorithmType
