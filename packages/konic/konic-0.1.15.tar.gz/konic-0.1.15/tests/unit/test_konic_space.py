import gymnasium as gym
import numpy as np
import pytest

from konic.common.errors import KonicAssertionError, KonicError
from konic.environment.space.space import KonicSpace
from konic.environment.space.type import KonicBound, KonicDiscrete, KonicMultiDiscrete


class TestKonicSpace:
    """Test cases for KonicSpace class."""

    def test_to_gym_with_discrete_field(self):
        """Test to_gym with a KonicDiscrete field."""

        class TestSpace(KonicSpace):
            action: KonicDiscrete = 5

        result = TestSpace.to_gym()
        expected = gym.spaces.Dict({"action": gym.spaces.Discrete(5)})
        assert result == expected

    def test_to_gym_with_bound_field(self):
        """Test to_gym with a KonicBound field."""

        class TestSpace(KonicSpace):
            position: KonicBound = ((2,), -1.0, 1.0)

        result = TestSpace.to_gym()
        expected = gym.spaces.Dict({"position": gym.spaces.Box(-1.0, 1.0, (2,), dtype=np.float32)})
        assert result == expected

    def test_to_gym_with_multiple_fields(self):
        """Test to_gym with multiple fields."""

        class TestSpace(KonicSpace):
            action: KonicDiscrete = 3
            position: KonicBound = ((1,), 0.0, 10.0)

        result = TestSpace.to_gym()
        expected = gym.spaces.Dict(
            {
                "action": gym.spaces.Discrete(3),
                "position": gym.spaces.Box(0.0, 10.0, (1,), dtype=np.float32),
            }
        )
        assert result == expected

    def test_to_gym_with_default_values(self):
        """Test to_gym with default values."""

        class TestSpace(KonicSpace):
            action: KonicDiscrete  # Uses default 2
            position: KonicBound  # Uses default ((1,), -1, 1)

        result = TestSpace.to_gym()
        expected = gym.spaces.Dict(
            {
                "action": gym.spaces.Discrete(2),
                "position": gym.spaces.Box(-1, 1, (1,), dtype=np.float32),
            }
        )
        assert result == expected

    def test_to_gym_unsupported_field_type(self):
        """Test that KonicError is raised for unsupported field types."""

        class TestSpace(KonicSpace):
            invalid_field: str = "test"

        with pytest.raises(KonicError, match="Unsupported field type"):
            TestSpace.to_gym()

    def test_to_gym_empty_space(self):
        """Test to_gym with no fields."""

        class TestSpace(KonicSpace):
            pass

        result = TestSpace.to_gym()
        expected = gym.spaces.Dict({})
        assert result == expected


class TestKonicMultiDiscrete:
    """Test cases for KonicMultiDiscrete type."""

    def test_to_gym_with_multidiscrete_default(self):
        """Test to_gym with KonicMultiDiscrete using default value."""

        class TestSpace(KonicSpace):
            actions: KonicMultiDiscrete

        result = TestSpace.to_gym()
        expected = gym.spaces.Dict({"actions": gym.spaces.MultiDiscrete([2, 2])})
        assert result == expected

    def test_to_gym_with_multidiscrete_custom_value(self):
        """Test to_gym with KonicMultiDiscrete using custom value."""

        class TestSpace(KonicSpace):
            actions: KonicMultiDiscrete = [3, 4, 5]

        result = TestSpace.to_gym()
        expected = gym.spaces.Dict({"actions": gym.spaces.MultiDiscrete([3, 4, 5])})
        assert result == expected

    def test_to_gym_with_multidiscrete_single_dimension(self):
        """Test to_gym with KonicMultiDiscrete using single dimension."""

        class TestSpace(KonicSpace):
            actions: KonicMultiDiscrete = [10]

        result = TestSpace.to_gym()
        expected = gym.spaces.Dict({"actions": gym.spaces.MultiDiscrete([10])})
        assert result == expected

    def test_to_gym_with_multidiscrete_large_dimensions(self):
        """Test to_gym with KonicMultiDiscrete using many dimensions."""

        class TestSpace(KonicSpace):
            actions: KonicMultiDiscrete = [2, 3, 4, 5, 6, 7, 8, 9, 10]

        result = TestSpace.to_gym()
        expected = gym.spaces.Dict(
            {"actions": gym.spaces.MultiDiscrete([2, 3, 4, 5, 6, 7, 8, 9, 10])}
        )
        assert result == expected

    def test_to_gym_with_multidiscrete_invalid_value_not_list(self):
        """Test that KonicAssertionError is raised when value is not a list."""

        class TestSpace(KonicSpace):
            actions: KonicMultiDiscrete = 5  # type: ignore

        with pytest.raises(
            KonicAssertionError, match="KonicMultiDiscrete type is not in a correct form"
        ):
            TestSpace.to_gym()

    def test_to_gym_with_multidiscrete_invalid_value_contains_one(self):
        """Test that KonicAssertionError is raised when list contains value <= 1."""

        class TestSpace(KonicSpace):
            actions: KonicMultiDiscrete = [3, 1, 5]

        with pytest.raises(
            KonicAssertionError, match="KonicMultiDiscrete type is not in a correct form"
        ):
            TestSpace.to_gym()

    def test_to_gym_with_multidiscrete_invalid_value_contains_zero(self):
        """Test that KonicAssertionError is raised when list contains zero."""

        class TestSpace(KonicSpace):
            actions: KonicMultiDiscrete = [2, 0, 3]

        with pytest.raises(
            KonicAssertionError, match="KonicMultiDiscrete type is not in a correct form"
        ):
            TestSpace.to_gym()

    def test_to_gym_with_multidiscrete_invalid_value_contains_negative(self):
        """Test that KonicAssertionError is raised when list contains negative value."""

        class TestSpace(KonicSpace):
            actions: KonicMultiDiscrete = [2, -1, 3]

        with pytest.raises(
            KonicAssertionError, match="KonicMultiDiscrete type is not in a correct form"
        ):
            TestSpace.to_gym()

    def test_to_gym_with_multiple_field_types_including_multidiscrete(self):
        """Test to_gym with multiple field types including KonicMultiDiscrete."""

        class TestSpace(KonicSpace):
            action: KonicDiscrete = 3
            position: KonicBound = ((2,), -1.0, 1.0)
            multi_action: KonicMultiDiscrete = [2, 3, 4]

        result = TestSpace.to_gym()
        expected = gym.spaces.Dict(
            {
                "action": gym.spaces.Discrete(3),
                "position": gym.spaces.Box(-1.0, 1.0, (2,), dtype=np.float32),
                "multi_action": gym.spaces.MultiDiscrete([2, 3, 4]),
            }
        )
        assert result == expected

    def test_to_gym_with_multiple_multidiscrete_fields(self):
        """Test to_gym with multiple KonicMultiDiscrete fields."""

        class TestSpace(KonicSpace):
            actions1: KonicMultiDiscrete = [2, 3]
            actions2: KonicMultiDiscrete = [4, 5, 6]

        result = TestSpace.to_gym()
        expected = gym.spaces.Dict(
            {
                "actions1": gym.spaces.MultiDiscrete([2, 3]),
                "actions2": gym.spaces.MultiDiscrete([4, 5, 6]),
            }
        )
        assert result == expected
