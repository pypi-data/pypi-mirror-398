import pytest

from konic.agent import KonicAgent
from konic.common.errors.cli import KonicValidationError
from konic.environment import KonicEnvironment
from konic.environment.reward import KonicRewardComposer
from konic.environment.space.space import KonicSpace
from konic.environment.space.type import KonicDiscrete
from konic.environment.termination import KonicTerminationComposer
from konic.runtime.agent import _perform_registration, get_registered_agent, register_agent
from konic.runtime.data import (
    DataDependency,
    clear_registered_data,
    get_registered_data,
    register_data,
)


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


class TestAgentRegistration:
    """Test cases for agent registration functionality."""

    def setup_method(self):
        """Reset global state before each test."""

        import konic.runtime.agent as runtime

        runtime._REGISTERED_AGENT_INSTANCE = None
        runtime._REGISTERED_ENV_CLASS = None

    def test_register_agent_success(self):
        """Test successful agent registration."""
        env = MockEnvironment()
        agent = KonicAgent(environment=env)
        agent_instance = agent

        result = register_agent(agent_instance, "test_agent")

        assert result is agent_instance
        registered_agent, registered_env = get_registered_agent()
        assert registered_agent is agent_instance
        assert registered_env is env
        assert hasattr(agent_instance, "_konic_meta")
        meta = getattr(agent_instance, "_konic_meta")
        assert meta["name"] == "test_agent"
        assert meta["env_module"] is env

    def test_register_agent_empty_name_raises_error(self):
        """Test that registering with empty name raises error."""
        env = MockEnvironment()
        agent = KonicAgent(environment=env)

        with pytest.raises(KonicValidationError, match="Agent name is required"):
            register_agent(agent, "")

    def test_register_agent_without_environment_raises_error(self):
        """Test that agent without environment raises error during registration."""
        agent = KonicAgent()

        with pytest.raises(Exception):
            register_agent(agent, "test_agent")

    def test_get_registered_agent_initially_none(self):
        """Test that initially no agent is registered."""
        agent, env = get_registered_agent()
        assert agent is None
        assert env is None

    def test_perform_registration_direct_call(self):
        """Test calling _perform_registration directly."""
        env = MockEnvironment()
        agent = KonicAgent(environment=env)

        result = _perform_registration(agent, "direct_test")

        assert result is agent
        registered_agent, registered_env = get_registered_agent()
        assert registered_agent is agent
        assert registered_env is env
        assert hasattr(agent, "_konic_meta")
        meta = getattr(agent, "_konic_meta")
        assert meta["name"] == "direct_test"

    def test_perform_registration_empty_name(self):
        """Test _perform_registration with empty name."""
        env = MockEnvironment()
        agent = KonicAgent(environment=env)

        with pytest.raises(KonicValidationError, match="Agent name is required"):
            _perform_registration(agent, "")


class TestDataRegistration:
    """Test cases for data registration functionality."""

    def setup_method(self):
        """Reset global state before each test."""
        clear_registered_data()

    def teardown_method(self):
        """Clean up after each test."""
        clear_registered_data()

    def test_register_data_success(self):
        """Test successful data registration."""
        result = register_data("stock-prices", "STOCK_DATA_PATH", "1.0.0")

        assert isinstance(result, DataDependency)
        assert result.cloud_name == "stock-prices"
        assert result.env_var == "STOCK_DATA_PATH"
        assert result.version == "1.0.0"

    def test_register_data_default_version(self):
        """Test data registration with default 'latest' version."""
        result = register_data("my-data", "MY_DATA_PATH")

        assert result.version == "latest"

    def test_register_data_normalizes_env_var(self):
        """Test that env_var is normalized to uppercase with underscores."""
        result = register_data("data", "my-data-path", "1.0.0")

        assert result.env_var == "MY_DATA_PATH"

    def test_register_data_normalizes_env_var_with_spaces(self):
        """Test that env_var handles spaces."""
        result = register_data("data", "my data path", "1.0.0")

        assert result.env_var == "MY_DATA_PATH"

    def test_register_data_multiple_registrations(self):
        """Test registering multiple data dependencies."""
        register_data("data-1", "DATA_1_PATH", "1.0.0")
        register_data("data-2", "DATA_2_PATH", "2.0.0")
        register_data("data-3", "DATA_3_PATH", "latest")

        deps = get_registered_data()
        assert len(deps) == 3
        assert deps[0].cloud_name == "data-1"
        assert deps[1].cloud_name == "data-2"
        assert deps[2].cloud_name == "data-3"

    def test_register_data_empty_cloud_name_raises_error(self):
        """Test that empty cloud_name raises validation error."""
        with pytest.raises(KonicValidationError, match="cloud_name is required"):
            register_data("", "DATA_PATH", "1.0.0")

    def test_register_data_empty_env_var_raises_error(self):
        """Test that empty env_var raises validation error."""
        with pytest.raises(KonicValidationError, match="env_var is required"):
            register_data("my-data", "", "1.0.0")

    def test_get_registered_data_initially_empty(self):
        """Test that initially no data is registered."""
        deps = get_registered_data()
        assert deps == []

    def test_get_registered_data_returns_copy(self):
        """Test that get_registered_data returns a copy, not the original list."""
        register_data("data-1", "DATA_PATH", "1.0.0")

        deps1 = get_registered_data()
        deps2 = get_registered_data()

        assert deps1 == deps2
        assert deps1 is not deps2  # Should be different list objects

    def test_clear_registered_data(self):
        """Test clearing registered data."""
        register_data("data-1", "DATA_1_PATH", "1.0.0")
        register_data("data-2", "DATA_2_PATH", "2.0.0")

        assert len(get_registered_data()) == 2

        clear_registered_data()

        assert len(get_registered_data()) == 0

    def test_data_dependency_is_frozen(self):
        """Test that DataDependency is immutable (frozen dataclass)."""
        dep = register_data("data", "DATA_PATH", "1.0.0")

        with pytest.raises(AttributeError):
            dep.cloud_name = "new-name"  # type: ignore

    def test_register_data_with_various_version_formats(self):
        """Test data registration with various version format strings."""
        versions = ["1.0.0", "v1", "2024-01-15", "latest", "beta-1", "1.0.0-rc1"]

        for i, version in enumerate(versions):
            result = register_data(f"data-{i}", f"DATA_{i}_PATH", version)
            assert result.version == version

    def test_register_data_preserves_order(self):
        """Test that data dependencies are retrieved in registration order."""
        names = ["alpha", "beta", "gamma", "delta"]
        for name in names:
            register_data(name, f"{name.upper()}_PATH", "1.0.0")

        deps = get_registered_data()
        retrieved_names = [dep.cloud_name for dep in deps]
        assert retrieved_names == names
