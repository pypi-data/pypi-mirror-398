import pytest

from konic.common.errors import KonicError
from konic.environment.termination import KonicTerminationComposer, custom_termination
from konic.environment.termination.reducers import OrReducerStrategy


class MockKonicTerminationComposer(KonicTerminationComposer):
    """Mock KonicTerminationComposer for testing."""

    def terminated(self) -> bool:
        return False


class TestKonicTerminationComposer:
    """Test cases for KonicTerminationComposer class."""

    @pytest.fixture
    def mock_termination_composer(self):
        return MockKonicTerminationComposer()

    def test_initialization(self, mock_termination_composer):
        """Test KonicTerminationComposer initialization."""
        assert mock_termination_composer.reducer == OrReducerStrategy

    def test_set_env(self, mock_termination_composer):
        """Test set_env method."""
        mock_env = object()
        mock_termination_composer.set_env(mock_env)
        assert mock_termination_composer.env is mock_env

    def test_terminated_base_method(self, mock_termination_composer):
        """Test base terminated method."""
        assert mock_termination_composer.terminated() is False

    def test_compose_without_custom_functions(self, mock_termination_composer):
        """Test compose method without custom termination functions."""
        result = mock_termination_composer.compose()
        assert result is False

    def test_compose_with_single_custom_function_true(self, mock_termination_composer):
        """Test compose with a single custom function returning True."""

        @custom_termination
        def custom_termination_fn(self) -> bool:
            return True

        mock_termination_composer.custom_termination = custom_termination_fn.__get__(
            mock_termination_composer, type(mock_termination_composer)
        )

        result = mock_termination_composer.compose()
        assert result is True

    def test_compose_with_single_custom_function_false(self, mock_termination_composer):
        """Test compose with a single custom function returning False."""

        @custom_termination
        def custom_termination_fn(self) -> bool:
            return False

        mock_termination_composer.custom_termination = custom_termination_fn.__get__(
            mock_termination_composer, type(mock_termination_composer)
        )

        result = mock_termination_composer.compose()
        assert result is False

    def test_compose_with_multiple_custom_functions_any_true(self, mock_termination_composer):
        """Test compose with multiple custom functions where at least one returns True."""

        @custom_termination
        def custom_termination_1(self) -> bool:
            return False

        @custom_termination
        def custom_termination_2(self) -> bool:
            return True

        @custom_termination
        def custom_termination_3(self) -> bool:
            return False

        mock_termination_composer.custom_termination_1 = custom_termination_1.__get__(
            mock_termination_composer, type(mock_termination_composer)
        )
        mock_termination_composer.custom_termination_2 = custom_termination_2.__get__(
            mock_termination_composer, type(mock_termination_composer)
        )
        mock_termination_composer.custom_termination_3 = custom_termination_3.__get__(
            mock_termination_composer, type(mock_termination_composer)
        )

        result = mock_termination_composer.compose()
        assert result is True

    def test_compose_with_multiple_custom_functions_all_false(self, mock_termination_composer):
        """Test compose with multiple custom functions where all return False."""

        @custom_termination
        def custom_termination_1(self) -> bool:
            return False

        @custom_termination
        def custom_termination_2(self) -> bool:
            return False

        mock_termination_composer.custom_termination_1 = custom_termination_1.__get__(
            mock_termination_composer, type(mock_termination_composer)
        )
        mock_termination_composer.custom_termination_2 = custom_termination_2.__get__(
            mock_termination_composer, type(mock_termination_composer)
        )

        result = mock_termination_composer.compose()
        assert result is False

    def test_compose_with_error_in_custom_function(self, mock_termination_composer):
        """Test compose handles errors in custom termination functions."""

        @custom_termination
        def custom_termination_with_error(self) -> bool:
            raise ValueError("Test error")

        mock_termination_composer.custom_termination_with_error = (
            custom_termination_with_error.__get__(
                mock_termination_composer, type(mock_termination_composer)
            )
        )

        with pytest.raises(KonicError, match="Error in custom termination function"):
            mock_termination_composer.compose()

    def test_unimplemented_terminated_raises_error(self):
        """Test that calling terminated on base composer without implementation raises error."""
        composer = KonicTerminationComposer()

        with pytest.raises(
            KonicError, match="KonicTerminationComposer.terminated\\(\\) is not implemented"
        ):
            composer.terminated()

    def test_custom_decorator_adds_attribute(self):
        """Test that @custom_termination decorator adds the correct attribute."""

        @custom_termination
        def test_function():
            return True

        assert hasattr(test_function, "_konic_custom_termination")
        assert getattr(test_function, "_konic_custom_termination") is True

    def test_compose_accesses_env(self, mock_termination_composer):
        """Test that custom functions can access the environment."""
        mock_env = type("MockEnv", (), {"test_value": 42})()
        mock_termination_composer.set_env(mock_env)

        @custom_termination
        def custom_termination_with_env(self) -> bool:
            return self.env.test_value > 40

        mock_termination_composer.custom_termination_with_env = custom_termination_with_env.__get__(
            mock_termination_composer, type(mock_termination_composer)
        )

        result = mock_termination_composer.compose()
        assert result is True
