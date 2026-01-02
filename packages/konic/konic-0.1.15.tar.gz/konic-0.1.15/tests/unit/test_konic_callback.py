"""Unit tests for the KonicRLCallback mechanism."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from konic.callback import KonicRLCallback, custom_metric
from konic.callback.enums import KonicCallbackKeys
from konic.callback.utils import get_custom_metric_fns


class MockMetricsLogger:
    """Mock MetricsLogger for testing."""

    def __init__(self):
        self.logged_values: dict[str, list] = {}

    def log_value(
        self,
        key: str,
        value: Any,
        reduce: str | None = None,
        window: int | None = None,
    ):
        if key not in self.logged_values:
            self.logged_values[key] = []
        self.logged_values[key].append(value)

    def get_logged_value(self, key: str):
        return self.logged_values.get(key, [])


class MockEpisode:
    """Mock SingleAgentEpisode for testing."""

    def __init__(
        self,
        return_value: float = 10.0,
        rewards: list[float] | None = None,
    ):
        self._return_value = return_value
        self._rewards = rewards or [1.0, 2.0, 3.0, 4.0]
        self.custom_data: dict[str, Any] = {}

    def get_return(self) -> float:
        return self._return_value

    def get_rewards(self) -> list[float]:
        return self._rewards


class MockAlgorithm:
    """Mock Algorithm for testing."""

    pass


class TestKonicCallbackEnums:
    """Test cases for KonicCallbackKeys enum."""

    def test_custom_metric_fn_attr_key_value(self):
        """Test CUSTOM_METRIC_FN_ATTR_KEY has correct value."""
        assert KonicCallbackKeys.CUSTOM_METRIC_FN_ATTR_KEY.value == "_konic_custom_metric_fn"

    def test_enum_is_string_enum(self):
        """Test that KonicCallbackKeys is a string enum."""
        assert isinstance(KonicCallbackKeys.CUSTOM_METRIC_FN_ATTR_KEY, str)


class TestCustomMetricDecorator:
    """Test cases for @custom_metric decorator."""

    def test_decorator_adds_attribute(self):
        """Test that @custom_metric decorator adds the correct attribute."""

        @custom_metric
        def test_function(self, episode):
            return {"test": 1.0}

        assert hasattr(test_function, "_konic_custom_metric_fn")
        assert getattr(test_function, "_konic_custom_metric_fn") is True

    def test_decorator_preserves_function_metadata(self):
        """Test that @custom_metric decorator preserves function name and docstring."""

        @custom_metric
        def my_custom_metric(self, episode) -> dict[str, float]:
            """This is a test docstring."""
            return {"metric": 1.0}

        assert my_custom_metric.__name__ == "my_custom_metric"
        assert my_custom_metric.__doc__ == "This is a test docstring."

    def test_decorated_function_is_callable(self):
        """Test that decorated function remains callable."""

        @custom_metric
        def test_metric(self, episode) -> dict[str, float]:
            return {"value": 42.0}

        mock_self = MagicMock()
        mock_episode = MockEpisode()

        result = test_metric(mock_self, mock_episode)
        assert result == {"value": 42.0}

    def test_decorator_returns_dict(self):
        """Test decorated function can return complex dict."""

        @custom_metric
        def multi_metric(self, episode) -> dict[str, float]:
            return {
                "metric_a": 1.0,
                "metric_b": 2.0,
                "metric_c": 3.0,
            }

        mock_self = MagicMock()
        mock_episode = MockEpisode()

        result = multi_metric(mock_self, mock_episode)
        assert result["metric_a"] == 1.0
        assert result["metric_b"] == 2.0
        assert result["metric_c"] == 3.0


class TestGetCustomMetricFns:
    """Test cases for get_custom_metric_fns utility."""

    def test_empty_instance_returns_empty_list(self):
        """Test that instance with no custom metrics returns empty list."""
        callback = KonicRLCallback()
        fns = get_custom_metric_fns(callback)
        assert fns == []

    def test_finds_custom_metric_methods(self):
        """Test that custom metric methods are discovered."""

        class CustomCallback(KonicRLCallback):
            @custom_metric
            def track_metric(self, episode) -> dict[str, float]:
                return {"test": 1.0}

        callback = CustomCallback()
        fns = get_custom_metric_fns(callback)
        assert len(fns) == 1
        assert fns[0].__name__ == "track_metric"

    def test_finds_multiple_custom_metrics(self):
        """Test that multiple custom metric methods are discovered."""

        class MultiMetricCallback(KonicRLCallback):
            @custom_metric
            def metric_one(self, episode) -> dict[str, float]:
                return {"one": 1.0}

            @custom_metric
            def metric_two(self, episode) -> dict[str, float]:
                return {"two": 2.0}

            @custom_metric
            def metric_three(self, episode) -> dict[str, float]:
                return {"three": 3.0}

        callback = MultiMetricCallback()
        fns = get_custom_metric_fns(callback)
        assert len(fns) == 3

    def test_ignores_non_decorated_methods(self):
        """Test that non-decorated methods are ignored."""

        class MixedCallback(KonicRLCallback):
            @custom_metric
            def tracked_metric(self, episode) -> dict[str, float]:
                return {"tracked": 1.0}

            def not_tracked(self, episode) -> dict[str, float]:
                return {"not_tracked": 2.0}

        callback = MixedCallback()
        fns = get_custom_metric_fns(callback)
        assert len(fns) == 1
        assert fns[0].__name__ == "tracked_metric"

    def test_ignores_private_methods(self):
        """Test that private methods (starting with _) are ignored."""

        class PrivateMethodCallback(KonicRLCallback):
            @custom_metric
            def _private_metric(self, episode) -> dict[str, float]:
                return {"private": 1.0}

            @custom_metric
            def public_metric(self, episode) -> dict[str, float]:
                return {"public": 2.0}

        callback = PrivateMethodCallback()
        fns = get_custom_metric_fns(callback)
        assert len(fns) == 1
        assert fns[0].__name__ == "public_metric"


class TestKonicRLCallback:
    """Test cases for KonicRLCallback class."""

    @pytest.fixture
    def callback(self):
        return KonicRLCallback()

    @pytest.fixture
    def metrics_logger(self):
        return MockMetricsLogger()

    @pytest.fixture
    def episode(self):
        return MockEpisode(return_value=50.0, rewards=[10.0, 20.0, 20.0])

    def test_initialization(self, callback):
        """Test KonicRLCallback initialization."""
        assert callback.total_episodes == 0
        assert callback.total_steps == 0
        assert callback.episode_returns == []
        assert callback.episode_lengths == []

    def test_on_episode_created_initializes_custom_data(self, callback, metrics_logger):
        """Test on_episode_created initializes custom data."""
        episode = MockEpisode()
        callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)

        assert "konic_step_rewards" in episode.custom_data
        assert "konic_step_count" in episode.custom_data
        assert episode.custom_data["konic_step_rewards"] == []
        assert episode.custom_data["konic_step_count"] == 0

    def test_on_episode_step_tracks_step_count(self, callback, metrics_logger):
        """Test on_episode_step increments step count."""
        episode = MockEpisode()
        callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)

        callback.on_episode_step(episode=episode, metrics_logger=metrics_logger)
        assert episode.custom_data["konic_step_count"] == 1

        callback.on_episode_step(episode=episode, metrics_logger=metrics_logger)
        assert episode.custom_data["konic_step_count"] == 2

    def test_on_episode_step_tracks_rewards(self, callback, metrics_logger):
        """Test on_episode_step tracks step rewards."""
        episode = MockEpisode(rewards=[5.0, 10.0, 15.0])
        callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)

        callback.on_episode_step(episode=episode, metrics_logger=metrics_logger)
        assert episode.custom_data["konic_step_rewards"] == [15.0]

    def test_on_episode_end_updates_global_tracking(self, callback, metrics_logger, episode):
        """Test on_episode_end updates global episode tracking."""
        callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
        callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        assert callback.total_episodes == 1
        assert 50.0 in callback.episode_returns

    def test_on_episode_end_logs_metrics(self, callback, metrics_logger, episode):
        """Test on_episode_end logs episode metrics."""
        callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
        callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        assert "konic/episode_return" in metrics_logger.logged_values
        assert "konic/episode_length" in metrics_logger.logged_values
        assert "konic/total_episodes" in metrics_logger.logged_values
        assert "konic/total_steps" in metrics_logger.logged_values

    def test_on_episode_end_multiple_episodes(self, callback, metrics_logger):
        """Test on_episode_end with multiple episodes."""
        for i in range(5):
            episode = MockEpisode(return_value=float(i * 10))
            callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
            callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        assert callback.total_episodes == 5
        assert len(callback.episode_returns) == 5
        assert callback.episode_returns == [0.0, 10.0, 20.0, 30.0, 40.0]

    def test_on_train_result_logs_throughput(self, callback, metrics_logger):
        """Test on_train_result logs throughput metrics."""
        algorithm = MockAlgorithm()
        result = {
            "time_total_s": 10.0,
            "num_env_steps_sampled_lifetime": 1000,
            "num_episodes_lifetime": 50,
            "training_iteration": 5,
        }

        callback.on_train_result(
            algorithm=algorithm,
            metrics_logger=metrics_logger,
            result=result,
        )

        assert "konic/throughput/fps" in metrics_logger.logged_values
        assert "konic/throughput/total_env_steps" in metrics_logger.logged_values
        assert "konic/throughput/total_episodes" in metrics_logger.logged_values
        assert "konic/throughput/training_iteration" in metrics_logger.logged_values

    def test_on_train_result_logs_learner_metrics(self, callback, metrics_logger):
        """Test on_train_result logs learner metrics."""
        algorithm = MockAlgorithm()
        result = {
            "learners": {
                "default_policy": {
                    "policy_loss": 0.5,
                    "vf_loss": 0.3,
                    "entropy": 0.1,
                    "kl": 0.01,
                    "curr_lr": 0.001,
                    "grad_gnorm": 1.5,
                }
            },
            "time_total_s": 10.0,
            "num_env_steps_sampled_lifetime": 1000,
        }

        callback.on_train_result(
            algorithm=algorithm,
            metrics_logger=metrics_logger,
            result=result,
        )

        assert "konic/learner/default_policy/policy_loss" in metrics_logger.logged_values
        assert "konic/learner/default_policy/value_loss" in metrics_logger.logged_values
        assert "konic/learner/default_policy/entropy" in metrics_logger.logged_values
        assert "konic/learner/default_policy/kl_divergence" in metrics_logger.logged_values
        assert "konic/learner/default_policy/learning_rate" in metrics_logger.logged_values
        assert "konic/learner/default_policy/grad_norm" in metrics_logger.logged_values

    def test_get_episode_returns(self, callback, metrics_logger):
        """Test get_episode_returns returns copy of returns list."""
        for i in range(3):
            episode = MockEpisode(return_value=float(i))
            callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
            callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        returns = callback.get_episode_returns()
        assert returns == [0.0, 1.0, 2.0]

        returns.append(100.0)
        assert callback.episode_returns == [0.0, 1.0, 2.0]

    def test_get_episode_lengths(self, callback, metrics_logger):
        """Test get_episode_lengths returns copy of lengths list."""
        for _ in range(3):
            episode = MockEpisode()
            callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
            callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        lengths = callback.get_episode_lengths()
        assert len(lengths) == 3

        original_len = len(callback.episode_lengths)
        lengths.append(100)
        assert len(callback.episode_lengths) == original_len

    def test_get_mean_return_empty(self, callback):
        """Test get_mean_return with no episodes returns 0.0."""
        assert callback.get_mean_return() == 0.0

    def test_get_mean_return_with_episodes(self, callback, metrics_logger):
        """Test get_mean_return calculates correct mean."""
        returns = [10.0, 20.0, 30.0, 40.0, 50.0]
        for r in returns:
            episode = MockEpisode(return_value=r)
            callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
            callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        mean = callback.get_mean_return()
        assert mean == 30.0  # (10 + 20 + 30 + 40 + 50) / 5

    def test_get_mean_return_with_window(self, callback, metrics_logger):
        """Test get_mean_return respects window parameter."""
        returns = [10.0, 20.0, 30.0, 40.0, 50.0]
        for r in returns:
            episode = MockEpisode(return_value=r)
            callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
            callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        mean = callback.get_mean_return(window=2)
        assert mean == 45.0  # (40 + 50) / 2

    def test_get_mean_length_empty(self, callback):
        """Test get_mean_length with no episodes returns 0.0."""
        assert callback.get_mean_length() == 0.0

    def test_get_mean_length_with_episodes(self, callback, metrics_logger):
        """Test get_mean_length calculates correct mean."""
        for _ in range(5):
            episode = MockEpisode(rewards=[1.0] * 10)  # 10 steps each
            callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
            for _ in range(10):
                callback.on_episode_step(episode=episode, metrics_logger=metrics_logger)
            callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        mean = callback.get_mean_length()
        assert mean == 10.0


class TestCustomCallbackWithMetrics:
    """Test cases for custom callbacks with @custom_metric decorator."""

    def test_custom_metric_logged_on_episode_end(self):
        """Test that custom metrics are logged when episode ends."""

        class MyCallback(KonicRLCallback):
            @custom_metric
            def track_custom(self, episode) -> dict[str, float]:
                return {"custom_value": 42.0}

        callback = MyCallback()
        metrics_logger = MockMetricsLogger()
        episode = MockEpisode()

        callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
        callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        assert "konic/custom/custom_value" in metrics_logger.logged_values
        assert metrics_logger.logged_values["konic/custom/custom_value"] == [42.0]

    def test_multiple_custom_metrics_logged(self):
        """Test that multiple custom metrics are all logged."""

        class MultiMetricCallback(KonicRLCallback):
            @custom_metric
            def metric_a(self, episode) -> dict[str, float]:
                return {"a": 1.0}

            @custom_metric
            def metric_b(self, episode) -> dict[str, float]:
                return {"b": 2.0}

        callback = MultiMetricCallback()
        metrics_logger = MockMetricsLogger()
        episode = MockEpisode()

        callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
        callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        assert "konic/custom/a" in metrics_logger.logged_values
        assert "konic/custom/b" in metrics_logger.logged_values

    def test_custom_metric_can_access_episode_data(self):
        """Test that custom metrics can access episode custom_data."""

        class DataAccessCallback(KonicRLCallback):
            @custom_metric
            def track_position(self, episode) -> dict[str, float]:
                return {"position": episode.custom_data.get("agent_x", 0.0)}

        callback = DataAccessCallback()
        metrics_logger = MockMetricsLogger()
        episode = MockEpisode()
        episode.custom_data["agent_x"] = 123.0

        callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
        callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        assert "konic/custom/position" in metrics_logger.logged_values
        assert metrics_logger.logged_values["konic/custom/position"] == [123.0]

    def test_custom_metric_error_does_not_crash(self, capsys):
        """Test that errors in custom metrics are handled gracefully."""

        class ErrorCallback(KonicRLCallback):
            @custom_metric
            def failing_metric(self, episode) -> dict[str, float]:
                raise ValueError("Test error")

        callback = ErrorCallback()
        metrics_logger = MockMetricsLogger()
        episode = MockEpisode()

        callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
        callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "failing_metric" in captured.out

    def test_custom_metric_returning_multiple_values(self):
        """Test custom metric returning dict with multiple values."""

        class MultiValueCallback(KonicRLCallback):
            @custom_metric
            def track_state(self, episode) -> dict[str, float]:
                return {
                    "velocity_x": 1.5,
                    "velocity_y": -2.0,
                    "angle": 45.0,
                }

        callback = MultiValueCallback()
        metrics_logger = MockMetricsLogger()
        episode = MockEpisode()

        callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
        callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        assert "konic/custom/velocity_x" in metrics_logger.logged_values
        assert "konic/custom/velocity_y" in metrics_logger.logged_values
        assert "konic/custom/angle" in metrics_logger.logged_values
        assert metrics_logger.logged_values["konic/custom/velocity_x"] == [1.5]
        assert metrics_logger.logged_values["konic/custom/velocity_y"] == [-2.0]
        assert metrics_logger.logged_values["konic/custom/angle"] == [45.0]

    def test_custom_metric_with_episode_return(self):
        """Test custom metric that uses episode return."""

        class ReturnBasedCallback(KonicRLCallback):
            @custom_metric
            def normalized_return(self, episode) -> dict[str, float]:
                return {"normalized": episode.get_return() / 100.0}

        callback = ReturnBasedCallback()
        metrics_logger = MockMetricsLogger()
        episode = MockEpisode(return_value=75.0)

        callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
        callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        assert "konic/custom/normalized" in metrics_logger.logged_values
        assert metrics_logger.logged_values["konic/custom/normalized"] == [0.75]


class TestCallbackInheritance:
    """Test cases for callback inheritance and overriding."""

    def test_subclass_can_override_on_episode_start(self):
        """Test that subclass can override on_episode_start."""
        started_episodes = []

        class CustomStartCallback(KonicRLCallback):
            def on_episode_start(self, *, episode, metrics_logger, **kwargs):
                started_episodes.append(episode)
                super().on_episode_start(episode=episode, metrics_logger=metrics_logger, **kwargs)

        callback = CustomStartCallback()
        metrics_logger = MockMetricsLogger()
        episode = MockEpisode()

        callback.on_episode_start(episode=episode, metrics_logger=metrics_logger)
        assert episode in started_episodes

    def test_subclass_can_override_on_episode_end(self):
        """Test that subclass can override on_episode_end while preserving metrics."""
        ended_episodes = []

        class CustomEndCallback(KonicRLCallback):
            def on_episode_end(self, *, episode, metrics_logger, **kwargs):
                ended_episodes.append(episode)
                super().on_episode_end(episode=episode, metrics_logger=metrics_logger, **kwargs)

        callback = CustomEndCallback()
        metrics_logger = MockMetricsLogger()
        episode = MockEpisode()

        callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
        callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        assert episode in ended_episodes
        assert "konic/episode_return" in metrics_logger.logged_values

    def test_subclass_can_add_state(self):
        """Test that subclass can add custom state."""

        class StatefulCallback(KonicRLCallback):
            def __init__(self):
                super().__init__()
                self.custom_counter = 0

            def on_episode_end(self, *, episode, metrics_logger, **kwargs):
                self.custom_counter += 1
                super().on_episode_end(episode=episode, metrics_logger=metrics_logger, **kwargs)

        callback = StatefulCallback()
        metrics_logger = MockMetricsLogger()

        for _ in range(5):
            episode = MockEpisode()
            callback.on_episode_created(episode=episode, metrics_logger=metrics_logger)
            callback.on_episode_end(episode=episode, metrics_logger=metrics_logger)

        assert callback.custom_counter == 5
        assert callback.total_episodes == 5


class TestThroughputMetrics:
    """Test cases for throughput metric logging."""

    def test_fps_calculation(self):
        """Test FPS is calculated correctly."""
        callback = KonicRLCallback()
        metrics_logger = MockMetricsLogger()
        algorithm = MockAlgorithm()

        result = {
            "time_total_s": 10.0,
            "num_env_steps_sampled_lifetime": 5000,
        }

        callback.on_train_result(
            algorithm=algorithm,
            metrics_logger=metrics_logger,
            result=result,
        )

        assert "konic/throughput/fps" in metrics_logger.logged_values
        assert metrics_logger.logged_values["konic/throughput/fps"] == [500.0]

    def test_fps_handles_zero_time(self):
        """Test FPS calculation handles zero time gracefully."""
        callback = KonicRLCallback()
        metrics_logger = MockMetricsLogger()
        algorithm = MockAlgorithm()

        result = {
            "time_total_s": 0.0,
            "num_env_steps_sampled_lifetime": 5000,
        }

        callback.on_train_result(
            algorithm=algorithm,
            metrics_logger=metrics_logger,
            result=result,
        )

        assert "konic/throughput/fps" in metrics_logger.logged_values

    def test_missing_throughput_metrics_handled(self):
        """Test that missing throughput metrics don't cause errors."""
        callback = KonicRLCallback()
        metrics_logger = MockMetricsLogger()
        algorithm = MockAlgorithm()

        result = {}  # Empty result

        callback.on_train_result(
            algorithm=algorithm,
            metrics_logger=metrics_logger,
            result=result,
        )


class TestLearnerMetrics:
    """Test cases for learner metric logging."""

    def test_all_learner_metrics_mapped(self):
        """Test all learner metrics are correctly mapped."""
        callback = KonicRLCallback()
        metrics_logger = MockMetricsLogger()
        algorithm = MockAlgorithm()

        result = {
            "learners": {
                "policy_0": {
                    "policy_loss": 0.123,
                    "vf_loss": 0.456,
                    "entropy": 0.789,
                    "kl": 0.012,
                    "curr_lr": 0.0003,
                    "grad_gnorm": 2.5,
                    "total_loss": 0.579,
                }
            },
            "time_total_s": 1.0,
            "num_env_steps_sampled_lifetime": 100,
        }

        callback.on_train_result(
            algorithm=algorithm,
            metrics_logger=metrics_logger,
            result=result,
        )

        assert metrics_logger.logged_values["konic/learner/policy_0/policy_loss"] == [0.123]
        assert metrics_logger.logged_values["konic/learner/policy_0/value_loss"] == [0.456]
        assert metrics_logger.logged_values["konic/learner/policy_0/entropy"] == [0.789]
        assert metrics_logger.logged_values["konic/learner/policy_0/kl_divergence"] == [0.012]
        assert metrics_logger.logged_values["konic/learner/policy_0/learning_rate"] == [0.0003]
        assert metrics_logger.logged_values["konic/learner/policy_0/grad_norm"] == [2.5]
        assert metrics_logger.logged_values["konic/learner/policy_0/total_loss"] == [0.579]

    def test_multiple_learners(self):
        """Test metrics are logged for multiple learners."""
        callback = KonicRLCallback()
        metrics_logger = MockMetricsLogger()
        algorithm = MockAlgorithm()

        result = {
            "learners": {
                "policy_0": {"policy_loss": 0.1},
                "policy_1": {"policy_loss": 0.2},
            },
            "time_total_s": 1.0,
            "num_env_steps_sampled_lifetime": 100,
        }

        callback.on_train_result(
            algorithm=algorithm,
            metrics_logger=metrics_logger,
            result=result,
        )

        assert "konic/learner/policy_0/policy_loss" in metrics_logger.logged_values
        assert "konic/learner/policy_1/policy_loss" in metrics_logger.logged_values

    def test_missing_learner_metrics_handled(self):
        """Test that missing learner metrics don't cause errors."""
        callback = KonicRLCallback()
        metrics_logger = MockMetricsLogger()
        algorithm = MockAlgorithm()

        result = {
            "learners": {
                "policy_0": {
                    "policy_loss": 0.1,
                }
            },
            "time_total_s": 1.0,
            "num_env_steps_sampled_lifetime": 100,
        }

        callback.on_train_result(
            algorithm=algorithm,
            metrics_logger=metrics_logger,
            result=result,
        )

        assert "konic/learner/policy_0/policy_loss" in metrics_logger.logged_values
        assert "konic/learner/policy_0/value_loss" not in metrics_logger.logged_values
