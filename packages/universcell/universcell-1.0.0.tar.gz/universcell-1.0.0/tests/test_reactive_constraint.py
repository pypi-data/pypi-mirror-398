"""
Unit tests for ReactiveConstraint primitive

Tests cover:
- Value change triggers
- Threshold breach detection
- Pattern matching (spike, drop, disconnect, timeout)
- Suppression strategies (cooldown, exponential backoff)
- State invalidation and re-evaluation
- Real-world scenarios (Gaming, Healthcare, Energy)
"""

import pytest
import time
from universalengine.primitives.reactive_constraint import (
    ReactiveConstraint,
    TriggerType,
    ConstraintStatus
)


class TestValueChangeTrigger:
    """Test constraints triggered by any value change"""
    
    def test_simple_value_change_invalidates(self):
        """Any value change should invalidate constraint"""
        rc = ReactiveConstraint(
            name="test",
            predicate="value >= 0",
            triggers={
                "type": "value_change",
                "watches": ["value"],
                "action": "re_evaluate"
            }
        )
        
        result = rc.on_state_change("value", 10, 20, timestamp=1000)
        
        assert result["invalidated"] == True
        assert result["needs_re_evaluation"] == True
    
    def test_no_change_doesnt_invalidate(self):
        """Same value should not invalidate"""
        rc = ReactiveConstraint(
            name="test",
            predicate="value >= 0",
            triggers={
                "type": "value_change",
                "watches": ["value"],
                "action": "re_evaluate"
            }
        )
        
        result = rc.on_state_change("value", 10, 10, timestamp=1000)
        
        assert result["invalidated"] == False
    
    def test_unwatched_field_ignored(self):
        """Changes to non-watched fields should be ignored"""
        rc = ReactiveConstraint(
            name="test",
            predicate="important >= 0",
            triggers={
                "type": "value_change",
                "watches": ["important"],
                "action": "re_evaluate"
            }
        )
        
        result = rc.on_state_change("unimportant", 10, 20, timestamp=1000)
        
        assert result["invalidated"] == False


class TestThresholdBreach:
    """Test threshold breach detection"""
    
    def test_breach_detected(self):
        """Crossing threshold from safe to unsafe should trigger"""
        rc = ReactiveConstraint(
            name="safe_zone",
            predicate="temp < 100",
            triggers={
                "type": "threshold_breach",
                "watches": ["temp"],
                "threshold": {"field": "temp", "value": 100},
                "action": "alert"
            }
        )
        
        # Cross from 95 to 105 (breach)
        result = rc.on_state_change("temp", 95, 105, timestamp=1000)
        
        assert result["invalidated"] == True
    
    def test_no_breach_within_threshold(self):
        """Staying within threshold should not trigger"""
        rc = ReactiveConstraint(
            name="safe_zone",
            predicate="temp < 100",
            triggers={
                "type": "threshold_breach",
                "threshold": {"field": "temp", "value": 100},
                "action": "alert"
            }
        )
        
        # Move from 90 to 95 (both safe)
        result = rc.on_state_change("temp", 90, 95, timestamp=1000)
        
        assert result["invalidated"] == False
    
    def test_no_breach_moving_away(self):
        """Moving from unsafe back to safe is not a breach"""
        rc = ReactiveConstraint(
            name="safe_zone",
            predicate="temp < 100",
            triggers={
                "type": "threshold_breach",
                "threshold": {"field": "temp", "value": 100},
                "action": "alert"
            }
        )
        
        # Move from 105 to 95 (recovery)
        result = rc.on_state_change("temp", 105, 95, timestamp=1000)
        
        assert result["invalidated"] == False


class TestPatternMatching:
    """Test pattern-based triggers"""
    
    def test_spike_pattern(self):
        """50% increase should be detected as spike"""
        rc = ReactiveConstraint(
            name="load_spike",
            predicate="load <= 1000",
            triggers={
                "type": "pattern_match",
                "pattern": "spike",
                "action": "redistribute"
            }
        )
        
        # 100 -> 160 is 60% increase (spike)
        result = rc.on_state_change("load", 100, 160, timestamp=1000)
        
        assert result["invalidated"] == True
    
    def test_no_spike_small_increase(self):
        """Small increase should not be spike"""
        rc = ReactiveConstraint(
            name="load_spike",
            predicate="load <= 1000",
            triggers={
                "type": "pattern_match",
                "pattern": "spike",
                "action": "redistribute"
            }
        )
        
        # 100 -> 120 is 20% increase (not spike)
        result = rc.on_state_change("load", 100, 120, timestamp=1000)
        
        assert result["invalidated"] == False
    
    def test_disconnect_pattern(self):
        """Disconnect pattern should trigger"""
        rc = ReactiveConstraint(
            name="player_connected",
            predicate="players_connected >= 2",
            triggers={
                "type": "pattern_match",
                "pattern": "disconnect",
                "action": "invalidate_match"
            }
        )
        
        result = rc.on_state_change("connected", True, False, timestamp=1000)
        
        assert result["invalidated"] == True


class TestStateTransition:
    """Test state machine transitions"""
    
    def test_transition_detected(self):
        """Specific state transition should trigger"""
        rc = ReactiveConstraint(
            name="match_state",
            predicate="state == 'playing'",
            triggers={
                "type": "state_transition",
                "from_state": "waiting",
                "to_state": "playing",
                "action": "start_match"
            }
        )
        
        result = rc.on_state_change("state", "waiting", "playing", timestamp=1000)
        
        assert result["invalidated"] == True
    
    def test_other_transition_ignored(self):
        """Different transitions should not trigger"""
        rc = ReactiveConstraint(
            name="match_state",
            predicate="state == 'playing'",
            triggers={
                "type": "state_transition",
                "from_state": "waiting",
                "to_state": "playing",
                "action": "start_match"
            }
        )
        
        result = rc.on_state_change("state", "playing", "finished", timestamp=1000)
        
        assert result["invalidated"] == False


class TestSuppressionCooldown:
    """Test cooldown suppression strategy"""
    
    def test_cooldown_suppression(self):
        """Suppression should prevent re-triggers during cooldown"""
        rc = ReactiveConstraint(
            name="alert",
            predicate="temp < 100",
            triggers={
                "type": "threshold_breach",
                "threshold": {"field": "temp", "value": 100},
                "action": "alert",
                "cooldown": 60
            },
            suppression_strategy="cooldown"
        )
        
        # First breach
        result1 = rc.on_state_change("temp", 95, 105, timestamp=1000)
        assert result1["invalidated"] == True
        
        # Second breach within cooldown (should be suppressed)
        result2 = rc.on_state_change("temp", 105, 110, timestamp=1010)
        assert result2["invalidated"] == False
        assert result2["reason"] == "Suppression active"
    
    def test_cooldown_expiry(self):
        """After cooldown expires, should allow re-trigger"""
        rc = ReactiveConstraint(
            name="alert",
            predicate="temp < 100",
            triggers={
                "type": "threshold_breach",
                "threshold": {"field": "temp", "value": 100},
                "action": "alert",
                "cooldown": 60
            },
            suppression_strategy="cooldown"
        )
        
        # First breach
        rc.on_state_change("temp", 95, 105, timestamp=1000)
        
        # Return to safe zone
        rc.on_state_change("temp", 105, 90, timestamp=1030)
        
        # Wait for cooldown to expire and breach again
        result = rc.on_state_change("temp", 90, 110, timestamp=1070)
        
        # Should now allow invalidation again
        assert result["invalidated"] == True


class TestSuppressionExponentialBackoff:
    """Test exponential backoff suppression"""
    
    def test_exponential_backoff(self):
        """Backoff should increase delay exponentially"""
        rc = ReactiveConstraint(
            name="alert",
            predicate="level >= 0",
            triggers={
                "type": "value_change",
                "watches": ["level"],
                "action": "alert",
                "backoff_base": 2,
                "max_backoff": 1000
            },
            suppression_strategy="exponential_backoff"
        )
        
        # First trigger
        rc.on_state_change("level", 0, 1, timestamp=1000)
        assert rc.suppression_active
        first_delay = rc.suppression_until - 1000
        
        # Second trigger (after first suppression expires)
        rc.on_state_change("level", 1, 2, timestamp=1000 + first_delay)
        second_delay = rc.suppression_until - (1000 + first_delay)
        
        # Second delay should be approximately 2x first
        assert second_delay > first_delay


class TestConstraintEvaluation:
    """Test constraint evaluation"""
    
    def test_satisfied_constraint(self):
        """Satisfied constraint should return True"""
        rc = ReactiveConstraint(
            name="test",
            predicate="value >= 10",
            triggers={"type": "value_change", "watches": ["value"]}
        )
        
        result = rc.evaluate(observations={"value": 20})
        
        assert result["satisfies"] == True
        assert result["status"] == "ACTIVE"
    
    def test_violated_constraint(self):
        """Violated constraint should return False"""
        rc = ReactiveConstraint(
            name="test",
            predicate="value >= 10",
            triggers={"type": "value_change", "watches": ["value"]}
        )
        
        result = rc.evaluate(observations={"value": 5})
        
        assert result["satisfies"] == False
    
    def test_evaluation_after_invalidation(self):
        """After invalidation, re-evaluation should update status"""
        rc = ReactiveConstraint(
            name="test",
            predicate="connected == True",
            triggers={
                "type": "pattern_match",
                "pattern": "disconnect",
                "watches": ["connected"],
                "action": "re_evaluate"
            }
        )
        
        # Trigger invalidation
        rc.on_state_change("connected", True, False, timestamp=1000)
        assert rc.status == ConstraintStatus.INVALIDATED
        
        # Evaluate when re-connected
        result = rc.evaluate(observations={"connected": True})
        assert result["status"] == "ACTIVE"
        assert result["satisfies"] == True


class TestRealWorldScenarios:
    """Test realistic domain scenarios"""
    
    def test_day5_gaming_match_validity(self):
        """Gaming: Match becomes invalid when player disconnects"""
        rc = ReactiveConstraint(
            name="match_validity",
            predicate="players_connected >= 2",
            triggers={
                "type": "pattern_match",
                "pattern": "drop",  # Detect player disconnect as a drop in count
                "watches": ["players_connected"],
                "action": "invalidate_match"
            },
            priority="critical"
        )
        
        # Both players connected
        result1 = rc.evaluate(observations={"players_connected": 2})
        assert result1["satisfies"] == True
        
        # Player 1 disconnects (2 -> 1 is 50% drop, triggers drop pattern)
        rc.on_state_change("players_connected", 2, 1, timestamp=1000)
        assert rc.status == ConstraintStatus.INVALIDATED
        
        # Evaluate with only 1 player
        result2 = rc.evaluate(observations={"players_connected": 1})
        assert result2["satisfies"] == False
        assert result2["status"] == "TRIGGERED"
    
    def test_day3_healthcare_sepsis_alert(self):
        """Healthcare: Multi-signal sepsis alert"""
        rc = ReactiveConstraint(
            name="sepsis_alert",
            predicate="o2_sat >= 90 OR (hr < 100 OR temp < 38.5)",
            triggers={
                "type": "threshold_breach",
                "threshold": {"field": "o2_sat", "value": 90},
                "action": "alert_physician"
            },
            priority="critical",
            suppression_strategy="cooldown"
        )
        
        # Critical values
        result = rc.evaluate(observations={
            "o2_sat": 88,
            "hr": 110,
            "temp": 39.2
        })
        
        assert result["satisfies"] == False
        assert result["priority"] == "critical"
    
    def test_day7_energy_load_spike(self):
        """Energy: Load spike triggers redistribution"""
        rc = ReactiveConstraint(
            name="load_stability",
            predicate="load <= 5000",
            triggers={
                "type": "pattern_match",
                "pattern": "spike",
                "watches": ["load"],
                "action": "redistribute_load"
            },
            priority="high"
        )
        
        # Baseline load
        result1 = rc.evaluate(observations={"load": 3000})
        assert result1["satisfies"] == True
        
        # Spike: 3000 -> 5100 (70% increase, over 50% threshold)
        rc.on_state_change("load", 3000, 5100, timestamp=1000)
        
        # After spike
        result2 = rc.evaluate(observations={"load": 5100})
        assert result2["satisfies"] == False


class TestMetrics:
    """Test metrics tracking"""
    
    def test_metrics_collection(self):
        """Metrics should track invalidations and evaluations"""
        rc = ReactiveConstraint(
            name="test",
            predicate="value >= 0",
            triggers={
                "type": "value_change",
                "watches": ["value"],
                "action": "re_evaluate"
            }
        )
        
        rc.on_state_change("value", 10, 20, timestamp=1000)
        rc.evaluate(observations={"value": 25})
        
        metrics = rc.get_metrics()
        
        assert metrics["invalidation_count"] == 1
        assert metrics["evaluation_count"] == 1
        assert metrics["status"] == "ACTIVE"


class TestReset:
    """Test reset functionality"""
    
    def test_reset_clears_state(self):
        """Reset should clear all tracking state"""
        rc = ReactiveConstraint(
            name="test",
            predicate="value >= 0",
            triggers={
                "type": "value_change",
                "watches": ["value"],
                "action": "re_evaluate"
            }
        )
        
        rc.on_state_change("value", 10, 20, timestamp=1000)
        rc.evaluate(observations={"value": 25})
        
        rc.reset()
        
        assert rc.evaluation_count == 0
        assert rc.invalidation_count == 0
        assert len(rc.trigger_history) == 0
        assert rc.status == ConstraintStatus.ACTIVE
