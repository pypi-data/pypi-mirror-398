import pytest

from konic.common.errors import KonicError
from konic.environment.reward import KonicRewardComposer, custom_reward
from konic.environment.reward.reducers import SumReducerStrategy


class MockKonicRewardComposer(KonicRewardComposer):
    """Mock KonicRewardComposer for testing."""

    def reward(self) -> float:
        return 0.0


class TestKonicRewardComposer:
    """Test cases for KonicRewardComposer class."""

    @pytest.fixture
    def mock_reward_composer(self):
        return MockKonicRewardComposer()

    def test_initialization(self, mock_reward_composer):
        """Test KonicRewardComposer initialization."""
        assert mock_reward_composer.reducer == SumReducerStrategy

    def test_set_env(self, mock_reward_composer):
        """Test set_env method."""
        mock_env = object()
        mock_reward_composer.set_env(mock_env)
        assert mock_reward_composer.env is mock_env

    def test_reward_base_method(self, mock_reward_composer):
        """Test base reward method."""
        assert mock_reward_composer.reward() == 0.0

    def test_compose_without_custom_functions(self, mock_reward_composer):
        """Test compose method without custom reward functions."""
        result = mock_reward_composer.compose()
        assert result == 0.0

    def test_compose_with_single_custom_function(self, mock_reward_composer):
        """Test compose with a single custom function returning a value."""

        @custom_reward
        def custom_reward_fn(self) -> float:
            return 10.0

        mock_reward_composer.custom_reward = custom_reward_fn.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )

        result = mock_reward_composer.compose()
        assert result == 10.0

    def test_compose_with_single_custom_function_negative(self, mock_reward_composer):
        """Test compose with a single custom function returning negative value."""

        @custom_reward
        def custom_reward_fn(self) -> float:
            return -5.0

        mock_reward_composer.custom_reward = custom_reward_fn.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )

        result = mock_reward_composer.compose()
        assert result == -5.0

    def test_compose_with_multiple_custom_functions(self, mock_reward_composer):
        """Test compose with multiple custom functions that get summed."""

        @custom_reward
        def custom_reward_1(self) -> float:
            return 10.0

        @custom_reward
        def custom_reward_2(self) -> float:
            return 20.0

        @custom_reward
        def custom_reward_3(self) -> float:
            return 5.5

        mock_reward_composer.custom_reward_1 = custom_reward_1.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )
        mock_reward_composer.custom_reward_2 = custom_reward_2.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )
        mock_reward_composer.custom_reward_3 = custom_reward_3.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )

        result = mock_reward_composer.compose()
        assert result == 35.5

    def test_compose_with_multiple_custom_functions_mixed_signs(self, mock_reward_composer):
        """Test compose with multiple custom functions with mixed positive and negative values."""

        @custom_reward
        def custom_reward_1(self) -> float:
            return 100.0

        @custom_reward
        def custom_reward_2(self) -> float:
            return -30.0

        @custom_reward
        def custom_reward_3(self) -> float:
            return -20.0

        mock_reward_composer.custom_reward_1 = custom_reward_1.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )
        mock_reward_composer.custom_reward_2 = custom_reward_2.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )
        mock_reward_composer.custom_reward_3 = custom_reward_3.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )

        result = mock_reward_composer.compose()
        assert result == 50.0

    def test_compose_with_error_in_custom_function(self, mock_reward_composer):
        """Test compose handles errors in custom reward functions."""

        @custom_reward
        def custom_reward_with_error(self) -> float:
            raise ValueError("Test error")

        mock_reward_composer.custom_reward_with_error = custom_reward_with_error.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )

        with pytest.raises(KonicError, match="Error in custom reward function"):
            mock_reward_composer.compose()

    def test_unimplemented_reward_raises_error(self):
        """Test that calling reward on base composer without implementation raises error."""
        composer = KonicRewardComposer()

        with pytest.raises(KonicError, match="KonicRewardComposer.reward\\(\\) is not implemented"):
            composer.reward()

    def test_custom_decorator_adds_attribute(self):
        """Test that @custom_reward decorator adds the correct attribute."""

        @custom_reward
        def test_function():
            return 1.0

        assert hasattr(test_function, "_konic_custom_reward")
        assert getattr(test_function, "_konic_custom_reward") is True

    def test_compose_accesses_env(self, mock_reward_composer):
        """Test that custom functions can access the environment."""
        mock_env = type("MockEnv", (), {"test_value": 42})()
        mock_reward_composer.set_env(mock_env)

        @custom_reward
        def custom_reward_with_env(self) -> float:
            return float(self.env.test_value)

        mock_reward_composer.custom_reward_with_env = custom_reward_with_env.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )

        result = mock_reward_composer.compose()
        assert result == 42.0

    def test_compose_with_zero_value_custom_functions(self, mock_reward_composer):
        """Test compose with custom functions that return zero."""

        @custom_reward
        def custom_reward_zero(self) -> float:
            return 0.0

        mock_reward_composer.custom_reward_zero = custom_reward_zero.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )

        result = mock_reward_composer.compose()
        assert result == 0.0

    def test_compose_with_float_precision(self, mock_reward_composer):
        """Test compose handles floating point precision correctly."""

        @custom_reward
        def custom_reward_1(self) -> float:
            return 0.1

        @custom_reward
        def custom_reward_2(self) -> float:
            return 0.2

        mock_reward_composer.custom_reward_1 = custom_reward_1.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )
        mock_reward_composer.custom_reward_2 = custom_reward_2.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )

        result = mock_reward_composer.compose()
        assert pytest.approx(result, rel=1e-9) == 0.3

    def test_compose_with_env_dependent_rewards(self, mock_reward_composer):
        """Test compose with multiple custom functions that depend on environment state."""
        mock_env = type("MockEnv", (), {"score": 100, "bonus": 50, "penalty": -10})()
        mock_reward_composer.set_env(mock_env)

        @custom_reward
        def score_reward(self) -> float:
            return float(self.env.score)

        @custom_reward
        def bonus_reward(self) -> float:
            return float(self.env.bonus)

        @custom_reward
        def penalty_reward(self) -> float:
            return float(self.env.penalty)

        mock_reward_composer.score_reward = score_reward.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )
        mock_reward_composer.bonus_reward = bonus_reward.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )
        mock_reward_composer.penalty_reward = penalty_reward.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )

        result = mock_reward_composer.compose()
        assert result == 140.0

    def test_custom_decorator_preserves_function_metadata(self):
        """Test that @custom_reward decorator preserves function name and docstring."""

        @custom_reward
        def my_custom_reward() -> float:
            """This is a test docstring."""
            return 1.0

        assert my_custom_reward.__name__ == "my_custom_reward"
        assert my_custom_reward.__doc__ == "This is a test docstring."

    def test_compose_without_set_env(self, mock_reward_composer):
        """Test compose works when env is not set (for custom functions not using env)."""

        @custom_reward
        def simple_reward(self) -> float:
            return 25.0

        mock_reward_composer.simple_reward = simple_reward.__get__(
            mock_reward_composer, type(mock_reward_composer)
        )

        result = mock_reward_composer.compose()
        assert result == 25.0
