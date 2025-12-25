from ray.rllib.algorithms import AlgorithmConfig
from ray.rllib.algorithms.ppo import PPOConfig

from konic.module.type import KonicAlgorithmType


def get_module_factory(algorithm: KonicAlgorithmType) -> type[AlgorithmConfig]:
    if algorithm == KonicAlgorithmType.PPO:
        return PPOConfig
