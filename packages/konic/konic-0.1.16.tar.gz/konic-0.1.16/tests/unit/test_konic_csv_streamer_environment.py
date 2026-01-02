"""
Unit tests for KonicCSVStreamerEnvironment
"""

import csv
import tempfile
from pathlib import Path

import pytest

from konic.common.errors import KonicError
from konic.environment import KonicCSVStreamerEnvironment
from konic.environment.reward import KonicRewardComposer
from konic.environment.space import KonicDiscrete, KonicSpace
from konic.environment.termination import KonicTerminationComposer


class MockActionSpace(KonicSpace):
    action: KonicDiscrete = 2


class MockRewardComposer(KonicRewardComposer):
    def compose(self) -> float:
        return 0.0


class MockTerminationComposer(KonicTerminationComposer):
    def compose(self) -> bool:
        return False


def create_test_csv(data: list[list[str]], include_header: bool = True) -> Path:
    """Create a temporary CSV file for testing."""
    temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv")
    writer = csv.writer(temp_file)

    if include_header:
        writer.writerow(["col1", "col2", "col3"])

    for row in data:
        writer.writerow(row)

    temp_file.close()
    return Path(temp_file.name)


class TestKonicCSVStreamerEnvironment:
    def test_basic_initialization(self):
        """Test basic initialization without sliding window."""
        test_data = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]
        csv_path = create_test_csv(test_data)

        try:
            env = KonicCSVStreamerEnvironment(
                csv_file_path=csv_path,
                action_space=MockActionSpace(),
                reward_composer=MockRewardComposer(),
                termination_composer=MockTerminationComposer(),
            )

            assert env.csv_file_path == csv_path
            assert len(env.csv_df) == 3
            assert env.current_index == 0

        finally:
            csv_path.unlink()

    def test_initialization_with_sliding_window(self):
        """Test initialization with sliding window."""
        test_data = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]
        csv_path = create_test_csv(test_data)

        try:
            env = KonicCSVStreamerEnvironment(
                csv_file_path=csv_path,
                action_space=MockActionSpace(),
                reward_composer=MockRewardComposer(),
                termination_composer=MockTerminationComposer(),
            )

            assert len(env.window_buffer) == 0

        finally:
            csv_path.unlink()

    def test_step_progression(self):
        """Test step functionality and progression through CSV data."""
        test_data = [["1", "2"], ["3", "4"], ["5", "6"]]
        csv_path = create_test_csv(test_data)

        try:
            env = KonicCSVStreamerEnvironment(
                csv_file_path=csv_path,
                action_space=MockActionSpace(),
                reward_composer=MockRewardComposer(),
                termination_composer=MockTerminationComposer(),
            )

            env.reset()

            obs, reward, terminated, truncated, info = env.step({"action": 0})
            assert env.current_index == 1
            assert not terminated
            assert not truncated

            obs, reward, terminated, truncated, info = env.step({"action": 0})
            assert env.current_index == 2
            assert not terminated
            assert not truncated

            obs, reward, terminated, truncated, info = env.step({"action": 0})
            assert env.current_index == 3
            assert not terminated
            assert truncated

        finally:
            csv_path.unlink()

    def test_file_not_found_error(self):
        """Test error handling for non-existent CSV file."""
        with pytest.raises(KonicError):
            KonicCSVStreamerEnvironment(
                csv_file_path="nonexistent.csv",
                action_space=MockActionSpace(),
                reward_composer=MockRewardComposer(),
                termination_composer=MockTerminationComposer(),
            )

    def test_properties(self):
        """Test environment properties."""
        test_data = [["1"], ["2"], ["3"]]
        csv_path = create_test_csv(test_data)

        try:
            env = KonicCSVStreamerEnvironment(
                csv_file_path=csv_path,
                action_space=MockActionSpace(),
                reward_composer=MockRewardComposer(),
                termination_composer=MockTerminationComposer(),
            )

            env.reset()

            assert not env.is_done
            assert env.remaining_rows == 3

            env.step({"action": 0})
            assert not env.is_done
            assert env.remaining_rows == 2

            env.step({"action": 0})
            env.step({"action": 0})
            assert env.is_done
            assert env.remaining_rows == 0

        finally:
            csv_path.unlink()

    def test_column_error_handling(self):
        """Test error handling for column operations."""
        test_data = [["1", "2"], ["3", "4"]]
        csv_path = create_test_csv(test_data)

        try:
            env = KonicCSVStreamerEnvironment(
                csv_file_path=csv_path,
                action_space=MockActionSpace(),
                reward_composer=MockRewardComposer(),
                termination_composer=MockTerminationComposer(),
            )

            env.reset()

            with pytest.raises(KonicError, match="Column 'invalid' not found"):
                env.get_column("invalid")

            with pytest.raises(KonicError, match="Column 'invalid' not found"):
                env.get_current_value("invalid")

            with pytest.raises(KonicError, match="Row index.*is out of bounds"):
                env.reset_to_row(100)

        finally:
            csv_path.unlink()
