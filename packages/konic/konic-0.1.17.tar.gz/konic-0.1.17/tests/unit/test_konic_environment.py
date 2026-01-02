import numpy as np
import pytest

from konic.environment.core import KonicEnvironment
from konic.environment.reward import KonicRewardComposer
from konic.environment.space.space import KonicSpace
from konic.environment.space.type import KonicBound, KonicDiscrete
from konic.environment.termination import KonicTerminationComposer


class MockActionSpace(KonicSpace):
    """Mock action space for testing."""

    action: KonicDiscrete = 3


class MockObservationSpace(KonicSpace):
    """Mock observation space for testing."""

    observation: KonicBound = ((2,), -1.0, 1.0)


class MockKonicRewardComposer(KonicRewardComposer):
    """Mock KonicRewardComposer for testing."""

    def reward(self) -> float:
        return 1.0


class MockKonicTerminationComposer(KonicTerminationComposer):
    """Mock KonicTerminationComposer for testing."""

    def terminated(self) -> bool:
        return False


class TestKonicEnvironment:
    """Test cases for KonicEnvironment class."""

    @pytest.fixture
    def mock_action_space(self) -> KonicSpace:
        return MockActionSpace()

    @pytest.fixture
    def mock_observation_space(self) -> KonicSpace:
        return MockObservationSpace()

    @pytest.fixture
    def mock_reward_composer(self):
        return MockKonicRewardComposer()

    @pytest.fixture
    def mock_termination_composer(self):
        return MockKonicTerminationComposer()

    @pytest.fixture
    def env(
        self,
        mock_action_space,
        mock_observation_space,
        mock_reward_composer,
        mock_termination_composer,
    ):
        class TestEnvironment(KonicEnvironment):
            def __init__(self):
                super().__init__(
                    action_space=mock_action_space,
                    observation_space=mock_observation_space,
                    reward_composer=mock_reward_composer,
                    termination_composer=mock_termination_composer,
                )
                self.test_state = np.array([0, 1])

            def reset(self, seed: int | None = None):
                obs = self.get_obs()
                info = self.get_info()

                return obs, info

            def step(self, action: KonicSpace):
                obs = self.get_obs()
                reward = self.reward_composer.compose()
                terminated = False
                truncated = False
                info = self.get_info()

                return obs, reward, terminated, truncated, info

            def get_obs(self):
                return self.test_state

        env = TestEnvironment()
        return env

    def test_initialization(
        self, env, mock_action_space, mock_observation_space, mock_reward_composer
    ):
        """Test KonicEnvironment initialization."""
        assert env._action_space == mock_action_space.to_gym()
        assert env._observation_space == mock_observation_space.to_gym()
        assert env._reward_composer == mock_reward_composer

    def test_action_space_property(self, env, mock_action_space):
        """Test action_space property."""
        expected = mock_action_space.to_gym()
        assert env.action_space == expected

    def test_observation_space_property(self, env, mock_observation_space):
        """Test observation_space property."""
        expected = mock_observation_space.to_gym()
        assert env.observation_space == expected

    def test_reward_composer_property(self, env, mock_reward_composer):
        """Test reward_composer property."""
        assert env.reward_composer == mock_reward_composer

    def test_step_valid_action(self, env):
        """Test step method with valid action."""
        action = {"action": 1}
        observation, reward, terminated, truncated, info = env.step(action)
        assert observation is not None
        assert isinstance(reward, (int | float))
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

    def test_reset_without_seed(self, env):
        """Test reset method without seed."""
        observation, info = env.reset()
        assert observation is not None
        assert isinstance(info, dict)

    def test_reset_with_seed(self, env):
        """Test reset method with seed."""
        observation, info = env.reset(seed=42)
        assert observation is not None
        assert isinstance(info, dict)

    def test_environment_with_termination_composer(
        self, mock_action_space, mock_observation_space, mock_reward_composer
    ):
        """Test KonicEnvironment with termination composer."""
        mock_termination_composer = MockKonicTerminationComposer()

        class TestEnvironmentWithTermination(KonicEnvironment):
            def __init__(self):
                super().__init__(
                    action_space=mock_action_space,
                    observation_space=mock_observation_space,
                    reward_composer=mock_reward_composer,
                    termination_composer=mock_termination_composer,
                )
                self.test_state = np.array([0, 1])

            def reset(self, seed: int | None = None):
                return self.get_obs(), self.get_info()

            def step(self, action):
                obs = self.get_obs()
                reward = self.reward_composer.compose()
                terminated = self.termination_composer.compose()
                truncated = False
                info = self.get_info()
                return obs, reward, terminated, truncated, info

            def get_obs(self):
                return self.test_state

        env = TestEnvironmentWithTermination()
        assert env.termination_composer == mock_termination_composer
        assert env.termination_composer.env == env

        action = env.action_space.sample()

        obs, reward, terminated, truncated, info = env.step(action)
        assert isinstance(terminated, bool)
        assert terminated is False
