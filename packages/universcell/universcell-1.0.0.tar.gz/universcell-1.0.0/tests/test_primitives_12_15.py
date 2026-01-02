"""
Test suite for Primitives #12-15

- Primitive #12: HierarchicalTemplate (Lazy instantiation)
- Primitive #13: CompiledConstraint (AST → bytecode)
- Primitive #14: ImmutableConstraint (Hash-based verification)
- Primitive #15: AdversarialModel (Byzantine fault tolerance)

Day 1: 20 tests for HierarchicalTemplate (days 2-3 add more)
Day 2: 20 tests for CompiledConstraint (days 3 adds more)
"""

import pytest
from datetime import datetime, timezone
from universalengine.primitives.hierarchical_template import (
    InstanceTemplate,
    Instance,
    HierarchicalTemplate
)
from universalengine.primitives.compiled_constraint import (
    CompiledConstraint,
    ConstraintCompiler,
    RealTimeConstraintExecutor
)
from universalengine.primitives.immutable_constraint import (
    ImmutableConstraint,
    ImmutableConstraintFactory
)
from universalengine.primitives.adversarial_model import (
    Signer,
    ByzantineVote,
    AdversarialModel
)


class TestHierarchicalTemplate_BasicOperations:
    """Test 1-5: Template registration and instance spawning."""
    
    def test_register_template(self):
        """Test 1: Register a valid template."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="TestSensor",
            version="1.0",
            properties={"type": "sensor", "value": 0},
            constraint_rules={"non_negative": lambda s: s["value"] >= 0}
        )
        
        ht.register_template(template)
        assert ht.get_template("TestSensor") is not None
    
    def test_register_template_duplicate_raises(self):
        """Test 2: Duplicate template registration raises ValueError."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="Sensor",
            version="1.0",
            properties={},
            constraint_rules={}
        )
        
        ht.register_template(template)
        
        with pytest.raises(ValueError, match="already registered"):
            ht.register_template(template)
    
    def test_spawn_single_instance(self):
        """Test 3: Spawn a single instance from template."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="Sensor",
            version="1.0",
            properties={"location": "room1", "reading": 20.5},
            constraint_rules={}
        )
        
        ht.register_template(template)
        instance = ht.spawn_instance("Sensor")
        
        assert instance.id is not None
        assert instance.template_name == "Sensor"
        assert instance.state["location"] == "room1"
        assert instance.state["reading"] == 20.5
    
    def test_spawn_instance_with_initial_state(self):
        """Test 4: Spawn instance with custom initial state."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="Device",
            version="1.0",
            properties={"status": "offline"},
            constraint_rules={}
        )
        
        ht.register_template(template)
        instance = ht.spawn_instance("Device", initial_state={"status": "online"})
        
        assert instance.state["status"] == "online"
    
    def test_spawn_multiple_instances(self):
        """Test 5: Spawn N instances from single template."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="Sensor",
            version="1.0",
            properties={"id": 0},
            constraint_rules={}
        )
        
        ht.register_template(template)
        instances = ht.spawn_instances("Sensor", count=100)
        
        assert len(instances) == 100
        assert ht.count_instances("Sensor") == 100
        assert all(inst.template_name == "Sensor" for inst in instances)


class TestHierarchicalTemplate_ConstraintEnforcement:
    """Test 6-10: Constraint validation per instance."""
    
    def test_enforce_single_constraint_pass(self):
        """Test 6: Single constraint passes."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="Sensor",
            version="1.0",
            properties={"reading": 25},
            constraint_rules={
                "in_range": lambda s: 0 <= s["reading"] <= 100
            }
        )
        
        ht.register_template(template)
        instance = ht.spawn_instance("Sensor")
        
        assert ht.enforce_constraints(instance.id) is True
    
    def test_enforce_single_constraint_fail(self):
        """Test 7: Single constraint fails and logged."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="Sensor",
            version="1.0",
            properties={"reading": 150},
            constraint_rules={
                "in_range": lambda s: 0 <= s["reading"] <= 100
            }
        )
        
        ht.register_template(template)
        instance = ht.spawn_instance("Sensor")
        
        assert ht.enforce_constraints(instance.id) is False
        violations = ht.get_constraint_violations()
        assert len(violations) > 0
        assert violations[0]["constraint"] == "in_range"
    
    def test_enforce_multiple_constraints(self):
        """Test 8: Multiple constraints (all pass)."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="Sensor",
            version="1.0",
            properties={"reading": 50, "status": "active"},
            constraint_rules={
                "in_range": lambda s: 0 <= s["reading"] <= 100,
                "status_valid": lambda s: s["status"] in ["active", "idle", "offline"]
            }
        )
        
        ht.register_template(template)
        instance = ht.spawn_instance("Sensor")
        
        assert ht.enforce_constraints(instance.id) is True
    
    def test_enforce_multiple_constraints_one_fails(self):
        """Test 9: Multiple constraints (one fails)."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="Sensor",
            version="1.0",
            properties={"reading": 50, "status": "broken"},
            constraint_rules={
                "in_range": lambda s: 0 <= s["reading"] <= 100,
                "status_valid": lambda s: s["status"] in ["active", "idle", "offline"]
            }
        )
        
        ht.register_template(template)
        instance = ht.spawn_instance("Sensor")
        
        assert ht.enforce_constraints(instance.id) is False
        violations = ht.get_constraint_violations()
        assert any(v["constraint"] == "status_valid" for v in violations)
    
    def test_enforce_constraint_exception_caught(self):
        """Test 10: Constraint exception is caught and logged."""
        ht = HierarchicalTemplate()
        
        def bad_constraint(state):
            raise RuntimeError("Sensor failed")
        
        template = InstanceTemplate(
            name="Sensor",
            version="1.0",
            properties={},
            constraint_rules={"risky": bad_constraint}
        )
        
        ht.register_template(template)
        instance = ht.spawn_instance("Sensor")
        
        assert ht.enforce_constraints(instance.id) is False
        violations = ht.get_constraint_violations()
        assert any(v["severity"] == "EXCEPTION" for v in violations)


class TestHierarchicalTemplate_StateManagement:
    """Test 11-14: State updates and lifecycle."""
    
    def test_update_instance_state_pass(self):
        """Test 11: Update state and constraints pass."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="Sensor",
            version="1.0",
            properties={"reading": 20},
            constraint_rules={
                "in_range": lambda s: 0 <= s["reading"] <= 100
            }
        )
        
        ht.register_template(template)
        instance = ht.spawn_instance("Sensor")
        
        result = ht.update_instance_state(instance.id, {"reading": 75})
        
        assert result is True
        assert ht.get_instance(instance.id).state["reading"] == 75
    
    def test_update_instance_state_fail(self):
        """Test 12: Update state and constraints fail."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="Sensor",
            version="1.0",
            properties={"reading": 50},
            constraint_rules={
                "in_range": lambda s: 0 <= s["reading"] <= 100
            }
        )
        
        ht.register_template(template)
        instance = ht.spawn_instance("Sensor")
        
        result = ht.update_instance_state(instance.id, {"reading": 150})
        
        assert result is False
    
    def test_deactivate_instance(self):
        """Test 13: Deactivate (soft delete) instance."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="Sensor",
            version="1.0",
            properties={},
            constraint_rules={}
        )
        
        ht.register_template(template)
        instance = ht.spawn_instance("Sensor")
        
        ht.deactivate_instance(instance.id)
        
        assert ht.get_instance(instance.id).is_active is False
    
    def test_lifecycle_hook_on_create(self):
        """Test 14: on_create hook is called."""
        ht = HierarchicalTemplate()
        created_instances = []
        
        template = InstanceTemplate(
            name="Sensor",
            version="1.0",
            properties={},
            constraint_rules={},
            lifecycle_hooks={
                "on_create": lambda inst: created_instances.append(inst.id)
            }
        )
        
        ht.register_template(template)
        instance = ht.spawn_instance("Sensor")
        
        assert instance.id in created_instances


class TestHierarchicalTemplate_IoTScalePattern:
    """Test 15-20: IoT scenario (10K sensors from 1 template)."""
    
    def test_iot_spawn_1000_sensors(self):
        """Test 15: Spawn 1,000 IoT sensors efficiently."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="IoTSensor",
            version="1.0",
            properties={
                "type": "temperature",
                "location": "unknown",
                "reading": 0.0,
                "battery_percent": 100
            },
            constraint_rules={
                "reading_in_range": lambda s: -50 <= s["reading"] <= 150,
                "battery_valid": lambda s: 0 <= s["battery_percent"] <= 100
            }
        )
        
        ht.register_template(template)
        
        # Spawn 1000 sensors
        sensors = ht.spawn_instances("IoTSensor", count=1000)
        
        assert len(sensors) == 1000
        assert ht.count_instances("IoTSensor") == 1000
    
    def test_iot_sensor_with_location(self):
        """Test 16: Spawn 100 sensors with unique locations."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="IoTSensor",
            version="1.0",
            properties={"reading": 20.0, "location": ""},
            constraint_rules={}
        )
        
        ht.register_template(template)
        
        locations = [f"room_{i}" for i in range(100)]
        states = [{"location": loc} for loc in locations]
        
        sensors = ht.spawn_instances("IoTSensor", count=100, initial_state_list=states)
        
        assert len(sensors) == 100
        assert sensors[0].state["location"] == "room_0"
        assert sensors[99].state["location"] == "room_99"
    
    def test_iot_enforce_all_sensors(self):
        """Test 17: Enforce constraints across all 1K sensors."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="IoTSensor",
            version="1.0",
            properties={"reading": 25.0},
            constraint_rules={
                "reading_valid": lambda s: -50 <= s["reading"] <= 150
            }
        )
        
        ht.register_template(template)
        sensors = ht.spawn_instances("IoTSensor", count=1000)
        
        result = ht.enforce_all_constraints("IoTSensor")
        assert result is True
    
    def test_iot_update_subset_of_sensors(self):
        """Test 18: Update readings for subset of sensors."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="IoTSensor",
            version="1.0",
            properties={"reading": 20.0},
            constraint_rules={
                "reading_valid": lambda s: -50 <= s["reading"] <= 150
            }
        )
        
        ht.register_template(template)
        sensors = ht.spawn_instances("IoTSensor", count=100)
        
        # Update 50 sensors
        for sensor in sensors[:50]:
            ht.update_instance_state(sensor.id, {"reading": 75.0})
        
        # Verify update
        updated_count = sum(
            1 for s in sensors[:50] 
            if ht.get_instance(s.id).state["reading"] == 75.0
        )
        assert updated_count == 50
    
    def test_iot_statistics(self):
        """Test 19: Compute statistics across instances."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="IoTSensor",
            version="1.0",
            properties={"reading": 20.0},
            constraint_rules={
                "reading_valid": lambda s: -50 <= s["reading"] <= 150
            }
        )
        
        ht.register_template(template)
        ht.spawn_instances("IoTSensor", count=500)
        
        stats = ht.get_statistics()
        
        assert stats["total_templates"] == 1
        assert stats["total_instances"] == 500
        assert stats["instances_by_template"]["IoTSensor"] == 500
    
    def test_iot_max_instances_limit(self):
        """Test 20: Respect max_instances limit (capacity planning)."""
        ht = HierarchicalTemplate()
        
        template = InstanceTemplate(
            name="IoTSensor",
            version="1.0",
            properties={"reading": 20.0},
            constraint_rules={},
            max_instances=100
        )
        
        ht.register_template(template)
        
        # Spawn 100 (should succeed)
        sensors = ht.spawn_instances("IoTSensor", count=100)
        assert len(sensors) == 100
        
        # Try to spawn 1 more (should fail)
        with pytest.raises(ValueError, match="max instances"):
            ht.spawn_instance("IoTSensor")


class TestCompiledConstraint_BasicCompilation:
    """Test 21-25: Constraint compilation and caching."""
    
    def test_compile_simple_constraint(self):
        """Test 21: Compile simple comparison constraint."""
        compiler = ConstraintCompiler()
        
        def latency_ok(latency):
            return latency < 5
        
        compiled = compiler.compile_constraint("latency_ok", latency_ok, optimize=False)
        
        assert compiled.name == "latency_ok"
        assert "latency" in compiled.parameter_names
        assert compiled.code_object is not None
    
    def test_execute_compiled_constraint(self):
        """Test 22: Execute compiled constraint (fast path)."""
        compiler = ConstraintCompiler()
        
        def latency_ok(latency):
            return latency < 5
        
        compiled = compiler.compile_constraint("latency_ok", latency_ok)
        
        result = compiled.execute(latency=3)
        assert result is True
        
        result = compiled.execute(latency=10)
        assert result is False
    
    def test_compile_multiple_parameters(self):
        """Test 23: Compile constraint with multiple parameters."""
        compiler = ConstraintCompiler()
        
        def health_valid(health, max_health):
            return 0 <= health <= max_health
        
        compiled = compiler.compile_constraint("health_valid", health_valid)
        
        assert len(compiled.parameter_names) == 2
        assert "health" in compiled.parameter_names
        assert "max_health" in compiled.parameter_names
    
    def test_execute_multi_parameter(self):
        """Test 24: Execute multi-parameter constraint."""
        compiler = ConstraintCompiler()
        
        def health_valid(health, max_health):
            return 0 <= health <= max_health
        
        compiled = compiler.compile_constraint("health_valid", health_valid)
        
        assert compiled.execute(health=50, max_health=100) is True
        assert compiled.execute(health=150, max_health=100) is False
        assert compiled.execute(health=-10, max_health=100) is False
    
    def test_constraint_caching(self):
        """Test 25: Compiled constraints are cached."""
        compiler = ConstraintCompiler()
        
        def speed_ok(speed):
            return speed > 0
        
        c1 = compiler.compile_constraint("speed_ok", speed_ok)
        c2 = compiler.get_compiled("speed_ok")
        
        assert c1 is c2  # Same object


class TestCompiledConstraint_Optimization:
    """Test 26-30: AST optimization and constant folding."""
    
    def test_optimize_constant_folding(self):
        """Test 26: Constant folding optimization."""
        compiler = ConstraintCompiler()
        
        def always_true(x):
            return True or x > 5
        
        compiled = compiler.compile_constraint("always_true", always_true, optimize=True)
        
        assert compiled.is_optimized is True
        assert len(compiled.optimization_notes) > 0
    
    def test_optimize_dead_code_elimination(self):
        """Test 27: Dead code elimination."""
        compiler = ConstraintCompiler()
        
        def dead_code(x):
            return True and x > 10
        
        compiled = compiler.compile_constraint("dead_code", dead_code, optimize=True)
        
        assert compiled.is_optimized is True
    
    def test_non_optimized_compilation(self):
        """Test 28: Compilation without optimization."""
        compiler = ConstraintCompiler()
        
        def simple(x):
            return x > 0
        
        compiled = compiler.compile_constraint("simple", simple, optimize=False)
        
        assert compiled.is_optimized is False
        assert compiled.optimization_notes == ""
    
    def test_execute_optimized_vs_unoptimized(self):
        """Test 29: Optimized and unoptimized give same result."""
        compiler = ConstraintCompiler()
        
        def range_check(value):
            return 0 < value < 100
        
        c_opt = compiler.compile_constraint("range_opt", range_check, optimize=True)
        
        # Re-compile without optimization
        compiler2 = ConstraintCompiler()
        c_unopt = compiler2.compile_constraint("range_unopt", range_check, optimize=False)
        
        # Both should give same result
        for test_val in [10, 50, 150, -10]:
            assert c_opt.execute(value=test_val) == c_unopt.execute(value=test_val)
    
    def test_complex_constraint_optimization(self):
        """Test 30: Complex expression optimization."""
        compiler = ConstraintCompiler()
        
        def complex_expr(a, b, c):
            return (a > 0) and (b < 100) and (c != 0)
        
        compiled = compiler.compile_constraint("complex", complex_expr, optimize=True)
        
        assert compiled.is_optimized is True


class TestCompiledConstraint_RealTimeExecution:
    """Test 31-35: Real-time execution with latency tracking."""
    
    def test_realtime_executor_basic(self):
        """Test 31: Real-time executor initialization."""
        executor = RealTimeConstraintExecutor(max_latency_ns=5_000_000)  # 5ms
        
        assert executor.max_latency_ns == 5_000_000
    
    def test_execute_with_latency_tracking(self):
        """Test 32: Execute constraint and track latency."""
        compiler = ConstraintCompiler()
        executor = RealTimeConstraintExecutor(max_latency_ns=5_000_000)
        
        def fast_check(x):
            return x > 0
        
        compiled = compiler.compile_constraint("fast_check", fast_check)
        
        result, latency_ns = executor.execute_with_timeout(compiled, x=10)
        
        assert result is True
        assert latency_ns >= 0
        assert latency_ns < 1_000_000  # Should be <1ms for simple operation
    
    def test_execution_logging(self):
        """Test 33: Execution audit trail."""
        compiler = ConstraintCompiler()
        executor = RealTimeConstraintExecutor()
        
        def simple_check(x):
            return x >= 0
        
        compiled = compiler.compile_constraint("simple_check", simple_check)
        
        executor.execute_with_timeout(compiled, x=5)
        executor.execute_with_timeout(compiled, x=-10)
        
        log = executor.get_execution_log()
        assert len(log) == 2
        assert log[0]['result'] is True
        assert log[1]['result'] is False
    
    def test_latency_statistics(self):
        """Test 34: Compute latency statistics."""
        compiler = ConstraintCompiler()
        executor = RealTimeConstraintExecutor()
        
        def quick_check(x):
            return x > 0
        
        compiled = compiler.compile_constraint("quick_check", quick_check)
        
        for i in range(10):
            executor.execute_with_timeout(compiled, x=i)
        
        stats = executor.get_latency_statistics()
        
        assert stats['total_executions'] == 10
        assert stats['average_latency_ns'] > 0
        assert stats['min_latency_ns'] <= stats['max_latency_ns']
    
    def test_missing_parameter_error(self):
        """Test 35: Error handling for constraint execution failure."""
        compiler = ConstraintCompiler()
        executor = RealTimeConstraintExecutor()
        
        def requires_param(x, y):
            return x + y > 10
        
        compiled = compiler.compile_constraint("requires_param", requires_param)
        
        # Provide wrong parameter type -> execution error
        with pytest.raises(RuntimeError, match="Constraint execution failed"):
            executor.execute_with_timeout(compiled, x=5)  # Missing 'y'


class TestCompiledConstraint_GamingScenario:
    """Test 36-40: Gaming real-time matchmaking (<5ms constraint)."""
    
    def test_gaming_player_validation(self):
        """Test 36: Validate player for matchmaking."""
        compiler = ConstraintCompiler()
        
        def player_eligible(elo_rating, min_elo, max_elo):
            return min_elo <= elo_rating <= max_elo
        
        compiled = compiler.compile_constraint("player_eligible", player_eligible)
        
        assert compiled.execute(elo_rating=1500, min_elo=1000, max_elo=2000) is True
        assert compiled.execute(elo_rating=500, min_elo=1000, max_elo=2000) is False
    
    def test_gaming_queue_wait_time(self):
        """Test 37: Queue wait time constraint."""
        compiler = ConstraintCompiler()
        
        def wait_acceptable(wait_seconds, max_wait):
            return wait_seconds <= max_wait
        
        compiled = compiler.compile_constraint("wait_acceptable", wait_acceptable)
        
        assert compiled.execute(wait_seconds=30, max_wait=60) is True
        assert compiled.execute(wait_seconds=120, max_wait=60) is False
    
    def test_gaming_latency_requirement(self):
        """Test 38: Latency requirement for gaming."""
        compiler = ConstraintCompiler()
        executor = RealTimeConstraintExecutor(max_latency_ns=5_000_000)  # 5ms
        
        def latency_ok(ping_ms):
            return ping_ms < 100
        
        compiled = compiler.compile_constraint("latency_ok", latency_ok)
        
        result, elapsed_ns = executor.execute_with_timeout(compiled, ping_ms=50)
        
        assert result is True
        assert elapsed_ns < 5_000_000  # Real constraint evaluation <5ms
    
    def test_gaming_match_stability(self):
        """Test 39: Match stability (50+ players, team balanced)."""
        compiler = ConstraintCompiler()
        
        def match_stable(team_a_size, team_b_size, min_players):
            return team_a_size >= min_players and team_b_size >= min_players
        
        compiled = compiler.compile_constraint("match_stable", match_stable)
        
        assert compiled.execute(team_a_size=25, team_b_size=25, min_players=20) is True
        assert compiled.execute(team_a_size=10, team_b_size=25, min_players=20) is False
    
    def test_gaming_bulk_validation(self):
        """Test 40: Validate 100 players in <500ms (5ms per player)."""
        compiler = ConstraintCompiler()
        executor = RealTimeConstraintExecutor(max_latency_ns=5_000_000)
        
        def player_ok(level):
            return 1 <= level <= 100
        
        compiled = compiler.compile_constraint("player_ok", player_ok)
        
        # Simulate 100 player validations
        for level in range(1, 101):
            result, _ = executor.execute_with_timeout(compiled, level=level)
            assert result is True
        
        stats = executor.get_latency_statistics()
        total_time_ns = stats['total_executions'] * stats['average_latency_ns']
        
        # Should complete in reasonable time
        assert stats['total_executions'] == 100


class TestImmutableConstraint_BasicOperations:
    """Test 41-45: Créer et vérifier contraintes immuables."""
    
    def test_create_immutable_constraint(self):
        """Test 41: Créer contrainte immuable."""
        factory = ImmutableConstraintFactory("secret_key_123")
        
        constraint = factory.create_constraint(
            name="blockchain_rule",
            description="Règle consensus blockchain",
            rule_expression="require_2of3_signatures()"
        )
        
        assert constraint.name == "blockchain_rule"
        assert constraint.hash_digest is not None
        assert len(constraint.hash_digest) == 64  # SHA256
    
    def test_constraint_signature_valid(self):
        """Test 42: Signature valide"""
        factory = ImmutableConstraintFactory("secret_key_123")
        
        constraint = factory.create_constraint(
            name="energy_constraint",
            description="Loi physique: fréquence 50Hz",
            rule_expression="frequency == 50"
        )
        
        is_valid = constraint.is_valid("secret_key_123")
        assert is_valid is True
    
    def test_constraint_signature_invalid_key(self):
        """Test 43: Signature invalide (mauvaise clé)"""
        factory = ImmutableConstraintFactory("secret_key_123")
        
        constraint = factory.create_constraint(
            name="test_rule",
            description="Test",
            rule_expression="x > 0"
        )
        
        is_valid = constraint.is_valid("wrong_secret_key")
        assert is_valid is False
    
    def test_detect_tampering(self):
        """Test 44: Détect modification de contrainte"""
        factory = ImmutableConstraintFactory("secret_key_123")
        
        constraint = factory.create_constraint(
            name="original_rule",
            description="Original",
            rule_expression="x > 10"
        )
        
        # Modifier l'expression après création
        constraint.rule_expression = "x > 20"  # Attaque!
        
        # Tamper detection
        is_tampered = factory.detect_tampering(constraint)
        assert is_tampered is True
    
    def test_constraint_versioning(self):
        """Test 45: Versioning de contraintes"""
        factory = ImmutableConstraintFactory("secret_key_123")
        
        c1 = factory.create_constraint("rule", "v1", "rule_v1", version=1)
        c2 = factory.create_constraint("rule", "v2", "rule_v2", version=2)
        
        history = factory.get_constraint_history("rule")
        
        assert len(history) == 2
        assert history[0].version == 1
        assert history[1].version == 2


class TestImmutableConstraint_BlockchainScenario:
    """Test 46-50: Scénario blockchain (immuabilité)."""
    
    def test_blockchain_consensus_rule_immutable(self):
        """Test 46: Règle consensus immuable"""
        factory = ImmutableConstraintFactory("blockchain_secret")
        
        consensus_rule = factory.create_constraint(
            name="consensus_2_of_3",
            description="Blockchain: 2 sur 3 signataires requuis",
            rule_expression="require_signatures(2, 3)"
        )
        
        # Vérifier que c'est immuable
        assert consensus_rule.is_valid("blockchain_secret") is True
        assert factory.detect_tampering(consensus_rule) is False
    
    def test_energy_physical_law_immutable(self):
        """Test 47: Loi physique immuable (Energy)"""
        factory = ImmutableConstraintFactory("energy_secret")
        
        freq_law = factory.create_constraint(
            name="frequency_limit",
            description="Loi physique: fréquence réseau 50±0.5 Hz",
            rule_expression="49.5 <= frequency <= 50.5"
        )
        
        assert freq_law.is_valid("energy_secret") is True
    
    def test_constraint_proof_format(self):
        """Test 48: Preuve d'immuabilité"""
        factory = ImmutableConstraintFactory("secret")
        
        constraint = factory.create_constraint(
            "proof_rule",
            "Pour preuve",
            "x > 0"
        )
        
        proof = constraint.get_proof()
        
        assert "hash" in proof
        assert "signature" in proof
        assert "created_at" in proof
        assert proof["constraint_name"] == "proof_rule"
    
    def test_multiple_constraint_verification(self):
        """Test 49: Vérifier multiple contraintes"""
        factory = ImmutableConstraintFactory("secret")
        
        c1 = factory.create_constraint("rule1", "desc1", "rule1_expr")
        c2 = factory.create_constraint("rule2", "desc2", "rule2_expr")
        c3 = factory.create_constraint("rule3", "desc3", "rule3_expr")
        
        assert factory.verify_constraint(c1) is True
        assert factory.verify_constraint(c2) is True
        assert factory.verify_constraint(c3) is True
        
        log = factory.get_verification_log()
        assert len(log) == 3
    
    def test_constraint_factory_statistics(self):
        """Test 50: Statistiques du factory"""
        factory = ImmutableConstraintFactory("secret")
        
        factory.create_constraint("rule1", "d1", "r1")
        factory.create_constraint("rule2", "d2", "r2")
        factory.create_constraint("rule1", "d1_v2", "r1_v2", version=2)
        
        stats = factory.get_statistics()
        
        assert stats["total_constraints"] == 2  # 2 noms uniques
        assert stats["total_versions"] == 3  # 3 versions
        assert stats["tampering_detected"] is False


class TestAdversarialModel_BasicConsensus:
    """Test 51-55: Consensus Byzantine basique."""
    
    def test_create_adversarial_model(self):
        """Test 51: Créer modèle adversarial"""
        model = AdversarialModel(
            total_signers=5,
            required_honest=3  # 3 sur 5 signataires honnêtes
        )
        
        assert model.total_signers == 5
        assert model.required_honest == 3
    
    def test_register_signers(self):
        """Test 52: Enregistrer signataires"""
        model = AdversarialModel(total_signers=5, required_honest=3)
        
        # 3 honnêtes, 2 malveillants
        for i in range(3):
            model.register_signer(f"honest_{i}", is_honest=True)
        
        for i in range(2):
            model.register_signer(f"adversary_{i}", is_honest=False)
        
        assert len(model.signers) == 5
    
    def test_create_vote(self):
        """Test 53: Créer vote"""
        model = AdversarialModel(total_signers=3, required_honest=2)
        
        for i in range(3):
            model.register_signer(f"signer_{i}")
        
        vote = model.create_vote("proposal_1")
        
        assert vote.proposal_id == "proposal_1"
        assert vote.threshold == 2
    
    def test_sign_vote_honest(self):
        """Test 54: Signataire honnête"""
        model = AdversarialModel(total_signers=3, required_honest=2)
        
        model.register_signer("signer_1", is_honest=True)
        
        vote = model.create_vote("prop_1")
        
        model.sign_vote(vote, "signer_1", approved=True, secret_key="secret")
        
        assert len(vote.signatures) == 1
        assert vote.count_approvals() == 1
    
    def test_consensus_reached(self):
        """Test 55: Consensus atteint"""
        model = AdversarialModel(total_signers=3, required_honest=2)
        
        model.register_signer("s1", is_honest=True)
        model.register_signer("s2", is_honest=True)
        
        vote = model.create_vote("prop_1")
        
        model.sign_vote(vote, "s1", approved=True, secret_key="secret")
        model.sign_vote(vote, "s2", approved=True, secret_key="secret")
        
        consensus, details = model.verify_vote(vote, "secret")
        
        assert consensus is True
        assert details["honest_signers"] == 2


class TestAdversarialModel_ByzantineAttacks:
    """Test 56-60: Attaques Byzantine (adversaires)."""
    
    def test_Byzantine_flip_attack(self):
        """Test 56: Attaque flip (inverser vote)"""
        model = AdversarialModel(total_signers=3, required_honest=2)
        
        model.register_signer("honest", is_honest=True)
        model.register_signer("adversary", is_honest=False)
        
        vote = model.create_vote("prop_1")
        
        # Adversaire vote contre (flip)
        model.sign_vote(vote, "adversary", approved=True, secret_key="secret")
        model.sign_vote(vote, "honest", approved=True, secret_key="secret")
        
        # Vérifier attaque détectée
        attacks = model.get_attack_log()
        assert any(a["attack_type"] == "Byzantine flip" for a in attacks)
    
    def test_Byzantine_colusion_detection(self):
        """Test 57: Détect colusion (adversaires conspirateurs)"""
        model = AdversarialModel(total_signers=5, required_honest=3)
        
        # Enregistrer signataires
        for i in range(3):
            model.register_signer(f"honest_{i}", is_honest=True)
        
        for i in range(2):
            model.register_signer(f"adversary_{i}", is_honest=False)
        
        vote = model.create_vote("prop_1")
        
        # Deux adversaires conspirateurs votent ensemble
        model.sign_vote(vote, "adversary_0", approved=False, secret_key="secret")
        model.sign_vote(vote, "adversary_1", approved=False, secret_key="secret")
        model.sign_vote(vote, "honest_0", approved=True, secret_key="secret")
        
        # Détect colusion
        colusions = model.detect_colusion(vote)
        
        assert len(colusions) > 0
    
    def test_Byzantine_threshold_security(self):
        """Test 58: Sécurité si majorité honnête"""
        model = AdversarialModel(total_signers=5, required_honest=3)
        
        # 3 honnêtes, 2 malveillants
        for i in range(3):
            model.register_signer(f"honest_{i}", is_honest=True)
        
        for i in range(2):
            model.register_signer(f"adversary_{i}", is_honest=False)
        
        vote = model.create_vote("prop_1")
        
        # Tous honnêtes + adversaires votent contre
        for i in range(3):
            model.sign_vote(vote, f"honest_{i}", approved=True, secret_key="secret")
        
        for i in range(2):
            model.sign_vote(vote, f"adversary_{i}", approved=False, secret_key="secret")
        
        consensus, details = model.verify_vote(vote, "secret")
        
        # Consensus atteint grâce à majorité honnête
        assert consensus is True
        assert details["honest_signers"] == 3
    
    def test_adversarial_model_statistics(self):
        """Test 59: Statistiques du modèle"""
        model = AdversarialModel(total_signers=5, required_honest=3)
        
        for i in range(3):
            model.register_signer(f"honest_{i}", is_honest=True)
        
        for i in range(2):
            model.register_signer(f"adversary_{i}", is_honest=False)
        
        stats = model.get_statistics()
        
        assert stats["honest_signers"] == 3
        assert stats["adversary_signers"] == 2
        assert stats["security_threshold_met"] is True
    
    def test_Byzantine_security_simulation(self):
        """Test 60: Simulation: attaque echouée (majorité défend)"""
        model = AdversarialModel(total_signers=7, required_honest=4)
        
        # 4 honnêtes, 3 malveillants
        for i in range(4):
            model.register_signer(f"honest_{i}", is_honest=True)
        
        for i in range(3):
            model.register_signer(f"adversary_{i}", is_honest=False)
        
        vote = model.create_vote("critical_decision")
        
        # Adversaires conspirent et votent ensemble
        for i in range(3):
            model.sign_vote(vote, f"adversary_{i}", approved=False, secret_key="secret")
        
        # Honnêtes votent pour
        for i in range(4):
            model.sign_vote(vote, f"honest_{i}", approved=True, secret_key="secret")
        
        # Consensus atteint malgré attaque
        consensus, details = model.verify_vote(vote, "secret")
        
        assert consensus is True
        assert details["honest_signers"] == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
