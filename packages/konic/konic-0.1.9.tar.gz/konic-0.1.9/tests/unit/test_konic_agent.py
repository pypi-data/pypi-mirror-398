import pytest

from konic.agent import KonicAgent
from konic.common.errors import KonicAssertionError, KonicConfigurationError
from konic.environment import KonicEnvironment
from konic.environment.reward import KonicRewardComposer
from konic.environment.space.space import KonicSpace
from konic.environment.space.type import KonicDiscrete
from konic.environment.termination import KonicTerminationComposer
from konic.module import BaseTorchModule, KonicTorchPPO


class MockActionSpace(KonicSpace):
    """Mock action space for testing."""

    action: KonicDiscrete = 3


class MockObservationSpace(KonicSpace):
    """Mock observation space for testing."""

    observation: KonicDiscrete = 5


class MockRewardComposer(KonicRewardComposer):
    """Mock reward composer for testing."""

    def reward(self) -> float:
        return 1.0


class MockTerminationComposer(KonicTerminationComposer):
    """Mock termination composer for testing."""

    def terminated(self) -> bool:
        return False


class MockEnvironment(KonicEnvironment):
    """Mock environment for testing."""

    def __init__(self):
        super().__init__(
            action_space=MockActionSpace(),
            observation_space=MockObservationSpace(),
            reward_composer=MockRewardComposer(),
            termination_composer=MockTerminationComposer(),
        )

    def reset(self):
        return {"observation": 0}

    def step(self, action):
        return {"observation": 1}, 1.0, False, False, {}


class MockModule(BaseTorchModule):
    """Mock module for testing."""

    pass


class TestKonicAgentDirectInstantiation:
    """Test cases for KonicAgent with direct instantiation."""

    def test_init_with_environment(self):
        """Test agent initialization with environment."""
        agent = KonicAgent(environment=MockEnvironment)
        assert agent.get_environment() == MockEnvironment

    def test_init_without_environment_raises_error(self):
        """Test that agent without environment raises error."""
        agent = KonicAgent()
        with pytest.raises(KonicConfigurationError, match="Environment must be provided"):
            agent.get_environment()

    def test_init_with_environment_config(self):
        """Test agent initialization with environment config."""
        config = {"param1": "value1", "param2": 42}
        agent = KonicAgent(environment=MockEnvironment, environment_config=config)
        assert agent.get_environment_config() == config

    def test_init_without_environment_config_returns_empty_dict(self):
        """Test agent without environment config returns empty dict."""
        agent = KonicAgent(environment=MockEnvironment)
        assert agent.get_environment_config() == {}

    def test_init_with_algorithm_config(self):
        """Test agent initialization with algorithm config."""
        config = {"lr": 0.001, "gamma": 0.99}
        agent = KonicAgent(environment=MockEnvironment, algorithm_config=config)
        assert agent.get_algorithm_config() == config

    def test_init_without_algorithm_config_returns_empty_dict(self):
        """Test agent without algorithm config returns empty dict."""
        agent = KonicAgent(environment=MockEnvironment)
        assert agent.get_algorithm_config() == {}

    def test_init_with_module(self):
        """Test agent initialization with module."""
        agent = KonicAgent(environment=MockEnvironment, module=MockModule)
        assert agent.get_module() is MockModule

    def test_init_without_module_returns_none(self):
        """Test agent without module returns default."""
        agent = KonicAgent(environment=MockEnvironment)
        assert agent.get_module() is KonicTorchPPO

    def test_init_with_training_config(self):
        """Test agent initialization with training config."""
        config = {"num_iterations": 1000, "batch_size": 32}
        agent = KonicAgent(environment=MockEnvironment, training_config=config)
        assert agent.get_training_config() == config

    def test_init_without_training_config_returns_empty_dict(self):
        """Test agent without training config returns empty dict."""
        agent = KonicAgent(environment=MockEnvironment)
        assert agent.get_training_config() == {}

    def test_init_with_all_params(self):
        """Test agent initialization with all parameters."""
        env_config = {"target": 10}
        algo_config = {"lr": 0.001}
        train_config = {"num_iterations": 500}

        agent = KonicAgent(
            environment=MockEnvironment,
            environment_config=env_config,
            algorithm_config=algo_config,
            module=MockModule,
            training_config=train_config,
        )

        assert agent.get_environment() == MockEnvironment
        assert agent.get_environment_config() == env_config
        assert agent.get_algorithm_config() == algo_config
        assert agent.get_module() is MockModule
        assert agent.get_training_config() == train_config


class TestKonicAgentSubclassing:
    """Test cases for KonicAgent with subclassing."""

    def test_subclass_with_overridden_methods(self):
        """Test agent subclass with all methods overridden."""

        class CustomAgent(KonicAgent):
            def get_environment(self):
                return MockEnvironment

            def get_environment_config(self):
                return {"custom": "config"}

            def get_algorithm_config(self):
                return {"lr": 0.002}

            def get_module(self):
                return MockModule

            def get_training_config(self):
                return {"num_iterations": 2000}

        agent = CustomAgent()
        assert agent.get_environment() == MockEnvironment
        assert agent.get_environment_config() == {"custom": "config"}
        assert agent.get_algorithm_config() == {"lr": 0.002}
        assert agent.get_module() is MockModule
        assert agent.get_training_config() == {"num_iterations": 2000}

    def test_subclass_with_partial_overrides(self):
        """Test agent subclass with only some methods overridden."""

        class PartialAgent(KonicAgent):
            def get_environment(self):
                return MockEnvironment

            def get_environment_config(self):
                return {"partial": "override"}

        agent = PartialAgent()
        assert agent.get_environment() == MockEnvironment
        assert agent.get_environment_config() == {"partial": "override"}
        assert agent.get_algorithm_config() == {}
        assert agent.get_module() is KonicTorchPPO
        assert agent.get_training_config() == {}

    def test_subclass_without_environment_raises_error(self):
        """Test agent subclass without environment override raises error."""

        class NoEnvAgent(KonicAgent):
            pass

        agent = NoEnvAgent()
        with pytest.raises(KonicConfigurationError, match="Environment must be provided"):
            agent.get_environment()

    def test_subclass_with_init_params_and_method_override(self):
        """Test that overridden methods are used even when init params are provided."""

        class CustomAgent(KonicAgent):
            def get_environment_config(self):
                return {"from": "method"}

        agent = CustomAgent(environment=MockEnvironment, environment_config={"from": "init"})

        assert agent.get_environment() == MockEnvironment
        assert agent.get_environment_config() == {"from": "method"}

    def test_subclass_can_call_super_to_use_init_params(self):
        """Test that subclass can use super() to access init params."""

        class CustomAgent(KonicAgent):
            def get_environment_config(self):
                base_config = super().get_environment_config()
                if base_config:
                    return base_config
                return {"from": "method"}

        agent = CustomAgent(environment=MockEnvironment, environment_config={"from": "init"})

        assert agent.get_environment() == MockEnvironment
        assert agent.get_environment_config() == {"from": "init"}

    def test_subclass_with_no_init_params_uses_methods(self):
        """Test that subclass without init params uses method implementations."""

        class CustomAgent(KonicAgent):
            def get_environment(self):
                return MockEnvironment

            def get_environment_config(self):
                return {"from": "method"}

        agent = CustomAgent()

        assert agent.get_environment() == MockEnvironment
        assert agent.get_environment_config() == {"from": "method"}


class TestKonicAgentEdgeCases:
    """Test edge cases for KonicAgent."""

    def test_empty_configs_are_mutable(self):
        """Test that empty configs don't share state between instances."""
        agent1 = KonicAgent(environment=MockEnvironment)
        agent2 = KonicAgent(environment=MockEnvironment)

        config1 = agent1.get_environment_config()
        config2 = agent2.get_environment_config()

        config1["test"] = "value"
        assert "test" not in config2

    def test_none_values_use_defaults(self):
        """Test that explicitly passing None uses default behavior."""
        agent = KonicAgent(
            environment=MockEnvironment,
            environment_config=None,
            algorithm_config=None,
            module=None,
            training_config=None,
        )

        assert agent.get_environment_config() == {}
        assert agent.get_algorithm_config() == {}
        assert agent.get_training_config() == {}
        with pytest.raises(KonicAssertionError, match="Module should not be None"):
            agent.get_module()
