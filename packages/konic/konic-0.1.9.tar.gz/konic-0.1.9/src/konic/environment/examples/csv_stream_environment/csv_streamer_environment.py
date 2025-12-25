"""
CSV Streamer Market Trading Environment Example

A market trading environment that streams data from a CSV file containing
market tick data (timestamp, OHLC, bid/ask, volume).

Actions:
    0: Hold position
    1: Buy
    2: Sell

Goal:
    Make profitable trades by analyzing streaming market data

Reward:
    - Positive reward for profitable trades
    - Negative reward for losses
    - Small penalty for holding to encourage action

Termination:
    - Episode ends when all CSV data is consumed
    - Episode ends when balance reaches zero (bankruptcy)
    - Episode ends after max_steps if specified
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from konic.environment import KonicCSVStreamerEnvironment
from konic.environment.reward import KonicRewardComposer, custom_reward
from konic.environment.space import KonicDiscrete, KonicSpace
from konic.environment.termination import KonicTerminationComposer


class MarketActionSpace(KonicSpace):
    action: KonicDiscrete = 2


class MarketRewardComposer(KonicRewardComposer["MarketTradingEnvironment"]):
    """Compose rewards based on trading performance."""

    @custom_reward
    def penalized_holds(self) -> float:
        return -0.5 if self.env.is_position else 0

    @custom_reward
    def pnl(self) -> float:
        current_price = self.env.get_obs()["close"].to_numpy(np.float32)

        if self.env.is_position is True and self.env.last_entry_price > current_price:
            return float((current_price - self.env.last_entry_price).item() * 1.3)

        if self.env.is_position is True and self.env.last_entry_price < current_price:
            return 1

        return 0


class MarketTerminationComposer(KonicTerminationComposer["MarketTradingEnvironment"]):
    def terminated(self) -> bool:
        """Base termination (always False, use custom conditions)."""
        return False


class MarketTradingEnvironment(KonicCSVStreamerEnvironment):
    """
    Market trading environment that streams market data from CSV.

    The environment simulates a simple trading scenario where an agent can
    buy, sell, or hold based on streaming market data.
    """

    def __init__(
        self,
        csv_file_path: str | Path,
        flatten_spaces: bool = False,
    ):
        """
        Initialize the market trading environment.

        Args:
            csv_file_path: Path to the CSV file containing market data
            flatten_spaces: If True, automatically flatten Dict spaces for RLlib compatibility
        """
        super().__init__(
            csv_file_path=csv_file_path,
            action_space=MarketActionSpace(),
            reward_composer=MarketRewardComposer(),
            termination_composer=MarketTerminationComposer(),
            flatten_spaces=flatten_spaces,
        )

        self.last_entry_price = 0
        self.last_exit_price = 0
        self.is_position = False
        self.total_reward = 0

    def _step(self, action):
        """Simple binary buy-and-sell step"""
        obs, reward, terminated, truncated, info = super()._step(action)

        if action["action"] == 1 and self.is_position is False:
            self.last_entry_price = obs["close"].to_numpy(np.float32)
            self.is_position = True

        if action["action"] == 0 and self.is_position is True:
            self.last_exit_price = obs["close"].to_numpy(np.float32)
            self.is_position = False

        self.total_reward += float(reward)
        return obs, reward, terminated, truncated, info

    def get_info(self) -> dict[str, Any]:
        current_price = self.get_obs()["close"].to_numpy(np.float32)
        return {
            "state": f"Entry price: {self.last_entry_price} - Exit price: {self.last_exit_price} - Position: {self.is_position} - Price: {current_price}"
        }


def main() -> None:
    """Run a simple example of the market trading environment."""

    csv_path = Path(__file__).parent / "market-1000.csv"

    env = MarketTradingEnvironment(
        csv_file_path=csv_path,
    )

    obs, info = env.reset(seed=42)

    for _ in range(100):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"Action: {action["action"]}", info, f"Reward: {env.total_reward}")


if __name__ == "__main__":
    main()
