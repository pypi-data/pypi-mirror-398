from typing import Any

import torch
import torch.nn as nn
from ray.rllib.core import Columns
from ray.rllib.core.rl_module.apis import ValueFunctionAPI
from ray.rllib.core.rl_module.torch import TorchRLModule
from ray.rllib.utils.annotations import override

from konic.module.base import BaseTorchModule
from konic.module.type import KonicAlgorithmType


class KonicTorchPPO(BaseTorchModule, TorchRLModule, ValueFunctionAPI):
    algorithm = KonicAlgorithmType.PPO

    @override(TorchRLModule)
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @override(TorchRLModule)
    def setup(self):
        super().setup()

        obs_space = self.config.observation_space
        action_space = self.config.action_space
        hidden_dim = int(self.model_config.get("hidden_dim", 64))

        in_dim = obs_space.shape[0]
        out_dim = int(action_space.n)

        self.pi = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, out_dim),
        )

        self.vf = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    @override(TorchRLModule)
    def _forward_inference(self, batch, **kwargs):
        with torch.no_grad():
            return self._forward_common(batch)

    @override(TorchRLModule)
    def _forward_exploration(self, batch, **kwargs):
        return self._forward_common(batch)

    @override(TorchRLModule)
    def _forward_train(self, batch, **kwargs):
        return self._forward_common(batch)

    def _forward_common(self, batch):
        """Common forward logic for all forward passes"""
        obs = batch[Columns.OBS]

        if len(obs.shape) == 1:
            obs = obs.unsqueeze(0)

        return {Columns.ACTION_DIST_INPUTS: self.pi(obs)}

    @override(ValueFunctionAPI)
    def compute_values(self, batch: dict[str, Any], embeddings: Any | None = None):
        obs = batch[Columns.OBS]

        if len(obs.shape) == 1:
            obs = obs.unsqueeze(0)

        return self.vf(obs).squeeze(-1)
