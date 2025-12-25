"""Tests for AI utilities"""
import time

import pytest

from praisonaiwp.ai.utils.cost_tracker import CostTracker
from praisonaiwp.ai.utils.rate_limiter import RateLimiter
from praisonaiwp.ai.utils.retry import retry_with_backoff


class TestCostTracker:
    """Test cost tracking"""

    def test_calculate_cost_gpt4o_mini(self):
        """Test cost calculation for gpt-4o-mini"""
        tracker = CostTracker()
        cost = tracker.calculate_cost('gpt-4o-mini', 1000, 1000)
        # (1000/1000 * 0.00015) + (1000/1000 * 0.0006) = 0.00075
        assert cost == 0.00075

    def test_calculate_cost_gpt4o(self):
        """Test cost calculation for gpt-4o"""
        tracker = CostTracker()
        cost = tracker.calculate_cost('gpt-4o', 1000, 1000)
        # (1000/1000 * 0.005) + (1000/1000 * 0.015) = 0.02
        assert cost == 0.02

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model defaults to gpt-4o-mini"""
        tracker = CostTracker()
        cost = tracker.calculate_cost('unknown-model', 1000, 1000)
        assert cost == 0.00075  # Same as gpt-4o-mini

    def test_track_generation(self):
        """Test tracking a generation"""
        tracker = CostTracker()
        result = tracker.track('gpt-4o-mini', 500, 500)

        assert result['model'] == 'gpt-4o-mini'
        assert result['input_tokens'] == 500
        assert result['output_tokens'] == 500
        assert result['total_tokens'] == 1000
        assert result['cost'] > 0

    def test_track_multiple_generations(self):
        """Test tracking multiple generations"""
        tracker = CostTracker()

        tracker.track('gpt-4o-mini', 500, 500)
        tracker.track('gpt-4o-mini', 1000, 1000)

        summary = tracker.get_summary()

        assert summary['total_generations'] == 2
        assert summary['total_input_tokens'] == 1500
        assert summary['total_output_tokens'] == 1500
        assert summary['total_cost'] > 0

    def test_get_summary_empty(self):
        """Test summary with no generations"""
        tracker = CostTracker()
        summary = tracker.get_summary()

        assert summary['total_generations'] == 0
        assert summary['total_cost'] == 0.0
        assert summary['average_cost'] == 0.0

    def test_reset(self):
        """Test resetting tracker"""
        tracker = CostTracker()
        tracker.track('gpt-4o-mini', 500, 500)

        tracker.reset()

        summary = tracker.get_summary()
        assert summary['total_generations'] == 0
        assert summary['total_cost'] == 0.0


class TestRateLimiter:
    """Test rate limiting"""

    def test_init(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter(max_requests=10, time_window=60)
        assert limiter.max_requests == 10
        assert limiter.time_window == 60

    def test_no_wait_under_limit(self):
        """Test no wait when under limit"""
        limiter = RateLimiter(max_requests=5, time_window=60)

        for _ in range(4):
            wait_time = limiter.wait_if_needed()
            assert wait_time is None

    def test_wait_when_over_limit(self):
        """Test waiting when over limit"""
        limiter = RateLimiter(max_requests=2, time_window=2)

        # Make 2 requests (at limit)
        limiter.wait_if_needed()
        limiter.wait_if_needed()

        # Third request should wait
        start = time.time()
        wait_time = limiter.wait_if_needed()
        elapsed = time.time() - start

        assert wait_time is not None
        assert elapsed >= 1.5  # Should wait ~2 seconds

    def test_get_remaining(self):
        """Test getting remaining requests"""
        limiter = RateLimiter(max_requests=5, time_window=60)

        assert limiter.get_remaining() == 5

        limiter.wait_if_needed()
        assert limiter.get_remaining() == 4

        limiter.wait_if_needed()
        assert limiter.get_remaining() == 3

    def test_reset(self):
        """Test resetting rate limiter"""
        limiter = RateLimiter(max_requests=5, time_window=60)

        limiter.wait_if_needed()
        limiter.wait_if_needed()

        limiter.reset()

        assert limiter.get_remaining() == 5


class TestRetryDecorator:
    """Test retry decorator"""

    def test_success_first_try(self):
        """Test successful execution on first try"""
        call_count = [0]

        @retry_with_backoff(max_retries=3)
        def success_func():
            call_count[0] += 1
            return "success"

        result = success_func()

        assert result == "success"
        assert call_count[0] == 1

    def test_success_after_retries(self):
        """Test successful execution after retries"""
        call_count = [0]

        @retry_with_backoff(max_retries=3, base_delay=0.1)
        def retry_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Temporary error")
            return "success"

        result = retry_func()

        assert result == "success"
        assert call_count[0] == 3

    def test_fail_after_max_retries(self):
        """Test failure after max retries"""
        call_count = [0]

        @retry_with_backoff(max_retries=3, base_delay=0.1)
        def fail_func():
            call_count[0] += 1
            raise ValueError("Permanent error")

        with pytest.raises(ValueError) as exc_info:
            fail_func()

        assert "Permanent error" in str(exc_info.value)
        assert call_count[0] == 3

    def test_exponential_backoff(self):
        """Test exponential backoff timing"""
        call_times = []

        @retry_with_backoff(max_retries=3, base_delay=0.1)
        def timed_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Retry")
            return "success"

        timed_func()

        # Check delays are increasing
        assert len(call_times) == 3
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        # Second delay should be ~2x first delay
        assert delay2 > delay1
        assert delay2 >= 0.15  # At least 0.2s (2^1 * 0.1)

    def test_specific_exceptions(self):
        """Test catching only specific exceptions"""
        @retry_with_backoff(
            max_retries=3,
            base_delay=0.1,
            exceptions=(ValueError,)
        )
        def specific_exception_func():
            raise TypeError("Wrong exception")

        with pytest.raises(TypeError):
            specific_exception_func()
