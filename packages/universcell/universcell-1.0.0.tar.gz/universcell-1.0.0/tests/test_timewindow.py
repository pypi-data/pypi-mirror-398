"""
Unit tests for TimeWindow primitive

Tests cover:
- Duration parsing (5m, 30d, 10s, etc)
- Window management (ring buffer)
- Aggregation functions (count, sum, avg, max, min, p95, p99)
- Constraint evaluation (<, >, <=, >=, ==, !=)
- Real-world scenarios (BGP, Finance, Energy)
"""

import pytest
from universalengine.primitives.timewindow import (
    TimeWindow,
    AggregationType,
    ConstraintStatus
)


class TestDurationParsing:
    """Test parsing of duration strings"""
    
    def test_parse_seconds(self):
        tw = TimeWindow("test", "var", "10s", "count", "value < 5")
        assert tw.window_seconds == 10.0
    
    def test_parse_minutes(self):
        tw = TimeWindow("test", "var", "5m", "count", "value < 5")
        assert tw.window_seconds == 300.0
    
    def test_parse_hours(self):
        tw = TimeWindow("test", "var", "1h", "count", "value < 5")
        assert tw.window_seconds == 3600.0
    
    def test_parse_days(self):
        tw = TimeWindow("test", "var", "30d", "count", "value < 5")
        assert tw.window_seconds == 2592000.0
    
    def test_parse_weeks(self):
        tw = TimeWindow("test", "var", "2w", "count", "value < 5")
        assert tw.window_seconds == 1209600.0
    
    def test_parse_decimal(self):
        tw = TimeWindow("test", "var", "2.5m", "count", "value < 5")
        assert tw.window_seconds == 150.0
    
    def test_parse_invalid_duration(self):
        with pytest.raises(ValueError):
            TimeWindow("test", "var", "invalid", "count", "value < 5")


class TestAggregationCount:
    """Test COUNT aggregation"""
    
    def test_count_single_event(self):
        tw = TimeWindow("test", "var", "1m", "count", "value < 5")
        
        result = tw.evaluate(timestamp=0, current_value=1)
        assert result["status"] == "VALID"
        assert result["aggregated_value"] == 1
        assert result["window_samples"] == 1
    
    def test_count_multiple_events(self):
        tw = TimeWindow("test", "var", "1m", "count", "value < 5")
        
        tw.add_observation(0, 1)
        tw.add_observation(10, 1)
        tw.add_observation(20, 1)
        
        result = tw.evaluate(timestamp=30)
        assert result["aggregated_value"] == 3
        assert result["satisfies_constraint"] == True  # 3 < 5
    
    def test_count_exceeds_limit(self):
        tw = TimeWindow("test", "var", "1m", "count", "value < 5")
        
        # Add 6 events (violates constraint)
        for i in range(6):
            tw.add_observation(i * 10, 1)
        
        result = tw.evaluate(timestamp=60)
        assert result["aggregated_value"] == 6
        assert result["satisfies_constraint"] == False  # 6 >= 5


class TestAggregationNumeric:
    """Test SUM, AVG, MAX, MIN aggregation"""
    
    def test_sum_aggregation(self):
        tw = TimeWindow("test", "var", "1m", "sum", "value < 20")
        
        tw.add_observation(0, 5)
        tw.add_observation(10, 7)
        tw.add_observation(20, 3)
        
        result = tw.evaluate(timestamp=30)
        assert result["aggregated_value"] == 15
        assert result["satisfies_constraint"] == True
    
    def test_avg_aggregation(self):
        tw = TimeWindow("test", "var", "1m", "avg", "value < 10")
        
        tw.add_observation(0, 5)
        tw.add_observation(10, 15)
        
        result = tw.evaluate(timestamp=20)
        assert result["aggregated_value"] == 10.0
        assert result["satisfies_constraint"] == False  # 10 >= 10
    
    def test_max_aggregation(self):
        tw = TimeWindow("test", "var", "1m", "max", "value < 20")
        
        tw.add_observation(0, 5)
        tw.add_observation(10, 18)
        tw.add_observation(20, 8)
        
        result = tw.evaluate(timestamp=30)
        assert result["aggregated_value"] == 18
        assert result["satisfies_constraint"] == True
    
    def test_min_aggregation(self):
        tw = TimeWindow("test", "var", "1m", "min", "value >= 5")
        
        tw.add_observation(0, 10)
        tw.add_observation(10, 5)
        tw.add_observation(20, 8)
        
        result = tw.evaluate(timestamp=30)
        assert result["aggregated_value"] == 5
        assert result["satisfies_constraint"] == True


class TestAggregationPercentile:
    """Test P95, P99 aggregation"""
    
    def test_p95_aggregation(self):
        tw = TimeWindow("test", "var", "1m", "p95", "value < 100")
        
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for i, v in enumerate(values):
            tw.add_observation(i * 6, v)
        
        result = tw.evaluate(timestamp=60)
        # p95 of [10..100] is approximately 95th percentile
        assert result["aggregated_value"] <= 95
        assert result["satisfies_constraint"] == True
    
    def test_p99_aggregation(self):
        tw = TimeWindow("test", "var", "1m", "p99", "value < 100")
        
        values = list(range(1, 101))  # 1-100
        for i, v in enumerate(values):
            tw.add_observation(i * 0.6, v)
        
        result = tw.evaluate(timestamp=60)
        assert result["aggregated_value"] <= 100


class TestWindowPruning:
    """Test that observations outside window are removed"""
    
    def test_old_observations_removed(self):
        tw = TimeWindow("test", "var", "10s", "count", "value < 100")
        
        # Add observations at t=0, 5, 10 seconds
        tw.add_observation(0, 1)
        tw.add_observation(5, 1)
        tw.add_observation(10, 1)
        
        # At t=15, only observations at 5 and 10 should remain (within 10s window)
        result = tw.evaluate(timestamp=15)
        assert result["window_samples"] == 2  # Only 2 recent observations
    
    def test_all_observations_outside_window(self):
        tw = TimeWindow("test", "var", "10s", "count", "value < 100")
        
        tw.add_observation(0, 1)
        tw.add_observation(5, 1)
        
        # At t=100, all observations are outside the window
        result = tw.evaluate(timestamp=100)
        assert result["status"] == "UNKNOWN"
        assert result["window_samples"] == 0


class TestConstraintEvaluation:
    """Test various constraint predicates"""
    
    def test_less_than(self):
        tw = TimeWindow("test", "var", "1m", "avg", "value < 10")
        tw.add_observation(0, 5)
        result = tw.evaluate(timestamp=10)
        assert result["satisfies_constraint"] == True
    
    def test_greater_than(self):
        tw = TimeWindow("test", "var", "1m", "avg", "value > 10")
        tw.add_observation(0, 15)
        result = tw.evaluate(timestamp=10)
        assert result["satisfies_constraint"] == True
    
    def test_less_than_or_equal(self):
        tw = TimeWindow("test", "var", "1m", "avg", "value <= 10")
        tw.add_observation(0, 10)
        result = tw.evaluate(timestamp=10)
        assert result["satisfies_constraint"] == True
    
    def test_greater_than_or_equal(self):
        tw = TimeWindow("test", "var", "1m", "avg", "value >= 10")
        tw.add_observation(0, 10)
        result = tw.evaluate(timestamp=10)
        assert result["satisfies_constraint"] == True
    
    def test_equal(self):
        tw = TimeWindow("test", "var", "1m", "count", "value == 3")
        tw.add_observation(0, 1)
        tw.add_observation(10, 1)
        tw.add_observation(20, 1)
        result = tw.evaluate(timestamp=30)
        assert result["satisfies_constraint"] == True
    
    def test_not_equal(self):
        tw = TimeWindow("test", "var", "1m", "count", "value != 5")
        tw.add_observation(0, 1)
        result = tw.evaluate(timestamp=10)
        assert result["satisfies_constraint"] == True  # 1 != 5


class TestRealWorldScenarios:
    """Test realistic domain scenarios"""
    
    def test_bgp_flap_rate_scenario(self):
        """Day 1: Max 5 flaps per 5 minutes"""
        tw = TimeWindow(
            name="bgp_flap_rate_5min",
            target_variable="flap_count",
            window_duration="5m",
            aggregation="count",
            constraint="value < 5"
        )
        
        # 3 flaps in first 2 minutes -> VALID
        tw.add_observation(0, 1)
        tw.add_observation(30, 1)
        tw.add_observation(60, 1)
        result = tw.evaluate(timestamp=120)
        assert result["satisfies_constraint"] == True
        
        # 2 more flaps -> 5 total -> VIOLATED
        tw.add_observation(180, 1)
        tw.add_observation(240, 1)
        result = tw.evaluate(timestamp=300)
        assert result["satisfies_constraint"] == False  # 5 >= 5
    
    def test_finance_drawdown_scenario(self):
        """Day 2: Max 5% drawdown per 30 days"""
        tw = TimeWindow(
            name="drawdown_max_30d",
            target_variable="drawdown_pct",
            window_duration="30d",
            aggregation="max",
            constraint="value <= 5.0"
        )
        
        # Simulate daily price changes
        # Day 1: 0.5% down
        tw.add_observation(0, 0.5)
        result = tw.evaluate(timestamp=86400)
        assert result["satisfies_constraint"] == True
        
        # Day 15: 3% down (cumulative)
        tw.add_observation(86400 * 14, 3.0)
        result = tw.evaluate(timestamp=86400 * 15)
        assert result["satisfies_constraint"] == True
        
        # Day 25: 6% down (VIOLATION)
        tw.add_observation(86400 * 24, 6.0)
        result = tw.evaluate(timestamp=86400 * 25)
        assert result["satisfies_constraint"] == False
    
    def test_energy_frequency_scenario(self):
        """Day 7: Grid frequency within ±0.5Hz per 10 seconds"""
        tw = TimeWindow(
            name="grid_frequency_deviation",
            target_variable="frequency_deviation_hz",
            window_duration="10s",
            aggregation="max",
            constraint="value <= 0.5"
        )
        
        # Normal operation: 0.1Hz deviation
        tw.add_observation(0, 0.1)
        tw.add_observation(2, 0.2)
        tw.add_observation(5, 0.15)
        result = tw.evaluate(timestamp=10)
        assert result["satisfies_constraint"] == True
        
        # Spike: 0.8Hz deviation -> VIOLATION
        tw.add_observation(12, 0.8)
        result = tw.evaluate(timestamp=15)
        assert result["satisfies_constraint"] == False


class TestMetrics:
    """Test internal metrics tracking"""
    
    def test_metrics_tracking(self):
        tw = TimeWindow("test", "var", "1m", "count", "value < 10")
        
        tw.add_observation(0, 1)
        tw.evaluate(timestamp=10)
        
        tw.add_observation(20, 1)
        tw.evaluate(timestamp=30)
        
        metrics = tw.get_metrics()
        assert metrics["evaluation_count"] == 2
        assert metrics["name"] == "test"
    
    def test_violation_tracking(self):
        tw = TimeWindow("test", "var", "1m", "count", "value < 2")
        
        # First evaluation: 1 < 2 -> VALID
        tw.add_observation(0, 1)
        tw.evaluate(timestamp=10)
        
        # Second evaluation: 2 < 2 -> VIOLATED
        tw.add_observation(20, 1)
        tw.evaluate(timestamp=30)
        
        # Third evaluation: 2 < 2 -> VIOLATED
        tw.evaluate(timestamp=35)
        
        metrics = tw.get_metrics()
        assert metrics["evaluation_count"] == 3
        assert metrics["violation_count"] == 2
        assert metrics["violation_rate"] == pytest.approx(0.667, abs=0.01)


class TestReset:
    """Test reset functionality"""
    
    def test_reset_clears_observations(self):
        tw = TimeWindow("test", "var", "1m", "count", "value < 100")
        
        tw.add_observation(0, 1)
        tw.add_observation(10, 1)
        tw.evaluate(timestamp=20)
        
        tw.reset()
        
        result = tw.evaluate(timestamp=30)
        assert result["window_samples"] == 0
        assert result["status"] == "UNKNOWN"
        assert tw.get_metrics()["evaluation_count"] == 0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_window_evaluation(self):
        tw = TimeWindow("test", "var", "1m", "count", "value < 5")
        
        result = tw.evaluate(timestamp=0)
        assert result["status"] == "UNKNOWN"
        assert result["window_samples"] == 0
    
    def test_single_observation(self):
        tw = TimeWindow("test", "var", "1m", "avg", "value < 100")
        
        tw.add_observation(0, 42)
        result = tw.evaluate(timestamp=10)
        assert result["aggregated_value"] == 42
        assert result["satisfies_constraint"] == True
    
    def test_stddev_with_single_value(self):
        tw = TimeWindow("test", "var", "1m", "stddev", "value == 0")
        
        tw.add_observation(0, 42)
        result = tw.evaluate(timestamp=10)
        assert result["aggregated_value"] == 0.0  # Single value has stddev=0
    
    def test_invalid_aggregation_type(self):
        with pytest.raises(ValueError):
            TimeWindow("test", "var", "1m", "invalid_agg", "value < 5")
    
    def test_invalid_constraint_expression(self):
        tw = TimeWindow("test", "var", "1m", "count", "value << 5")  # Invalid operator
        
        tw.add_observation(0, 1)
        with pytest.raises(ValueError):
            tw.evaluate(timestamp=10)
