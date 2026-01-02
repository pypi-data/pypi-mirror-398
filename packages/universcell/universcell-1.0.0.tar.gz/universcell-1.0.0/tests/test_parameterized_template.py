"""
Unit tests for ParameterizedTemplate primitive

Tests cover:
- Template substitution with parameters
- Cartesian product generation (50 × 5 = 250+)
- Instance ID generation
- Evaluation of all instances
- Real-world scenarios (IoT, Gaming, Finance)
"""

import pytest
from universalengine.primitives.parameterized_template import (
    ParameterizedTemplate,
    TemplateFactory,
    GenerationStrategy
)


class TestBasicSubstitution:
    """Test parameter substitution"""
    
    def test_simple_substitution(self):
        """Replace {param} with values"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={
                "room": "ROOM_101",
                "sensor": "temp",
                "min": 20,
                "max": 25
            },
            constraint_template="{room}_{sensor}: value >= {min} AND value <= {max}"
        )
        
        config = template.parameter_set
        result = template._substitute_template(config)
        assert result == "ROOM_101_temp: value >= 20 AND value <= 25"
    
    def test_missing_parameter(self):
        """Error if template references non-existent parameter"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={"room": "R1"},
            constraint_template="{room}_{sensor}: test"
        )
        
        with pytest.raises(ValueError):
            template._substitute_template({"room": "R1"})
    
    def test_numeric_substitution(self):
        """Numeric parameters converted to strings"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={
                "id": 42,
                "threshold": 99.5
            },
            constraint_template="constraint_{id}: value < {threshold}"
        )
        
        config = template.parameter_set
        result = template._substitute_template(config)
        assert result == "constraint_42: value < 99.5"


class TestInstanceIDGeneration:
    """Test instance ID creation"""
    
    def test_id_from_config(self):
        """Generate unique ID from config"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={},
            constraint_template=""
        )
        
        config = {"room": "R101", "sensor": "temp"}
        iid = template._make_instance_id(config)
        assert iid == "R101_temp"
    
    def test_id_multiple_params(self):
        """ID from multiple parameters (sorted)"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={},
            constraint_template=""
        )
        
        config = {"z": "Z", "a": "A", "m": "M"}
        iid = template._make_instance_id(config)
        # Sorted order: a, m, z
        assert iid == "A_M_Z"
    
    def test_id_with_spaces(self):
        """Spaces converted to underscores"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={},
            constraint_template=""
        )
        
        config = {"room": "ROOM 101", "sensor": "temperature"}
        iid = template._make_instance_id(config)
        assert iid == "ROOM_101_temperature"


class TestCartesianProduct:
    """Test Cartesian product generation"""
    
    def test_simple_cartesian(self):
        """2 × 2 Cartesian product"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={
                "room": ["R1", "R2"],
                "sensor": ["T", "H"]
            },
            constraint_template="{room}_{sensor}",
            generation_strategy="cartesian_product"
        )
        
        configs = template._generate_cartesian()
        assert len(configs) == 4
        
        expected_ids = {"R1_T", "R1_H", "R2_T", "R2_H"}
        actual_ids = {
            f"{c['room']}_{c['sensor']}" for c in configs
        }
        assert actual_ids == expected_ids
    
    def test_cartesian_with_scalars(self):
        """Mix of list and scalar parameters"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={
                "room": ["R1", "R2"],
                "sensor": ["temp"],  # List with 1 item
                "min": 20,           # Scalar
                "max": 25            # Scalar
            },
            constraint_template="",
            generation_strategy="cartesian_product"
        )
        
        configs = template._generate_cartesian()
        assert len(configs) == 2  # 2 rooms × 1 sensor
        
        # Each config should have all parameters
        assert all("min" in c and c["min"] == 20 for c in configs)
        assert all("max" in c and c["max"] == 25 for c in configs)
    
    def test_large_cartesian(self):
        """IoT scenario: 50 rooms × 5 sensors = 250 instances"""
        rooms = [f"ROOM_{i:03d}" for i in range(50)]
        sensors = ["temp", "humidity", "co2", "light", "occupancy"]
        
        template = ParameterizedTemplate(
            name="iot_sensors",
            parameter_set={
                "room": rooms,
                "sensor": sensors,
                "min": 0,
                "max": 100
            },
            constraint_template="{room}_{sensor}: value >= {min} AND value <= {max}",
            generation_strategy="cartesian_product"
        )
        
        count = template.generate_all_instances()
        assert count == 250


class TestInstanceGeneration:
    """Test full instance generation"""
    
    def test_generate_all_instances(self):
        """Generate constraints from template"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={
                "id": ["A", "B"],
                "type": ["X", "Y"],
                "threshold": 100
            },
            constraint_template="{id}_{type}: value < {threshold}",
            generation_strategy="cartesian_product"
        )
        
        count = template.generate_all_instances()
        assert count == 4  # 2 × 2
        
        # Check all instances generated
        assert "A_X" in template.generated_constraints
        assert "A_Y" in template.generated_constraints
        assert "B_X" in template.generated_constraints
        assert "B_Y" in template.generated_constraints
    
    def test_get_instance(self):
        """Retrieve specific constraint instance"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={
                "room": ["R1"],
                "sensor": ["temp"]
            },
            constraint_template="{room}_{sensor}: value < 30",
            generation_strategy="cartesian_product"
        )
        
        template.generate_all_instances()
        
        instance = template.get_instance("R1_temp")
        assert instance is not None
        assert instance["predicate"] == "R1_temp: value < 30"
    
    def test_get_instances_by_parameter(self):
        """Find all constraints with specific parameter value"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={
                "room": ["R1", "R2", "R3"],
                "sensor": ["temp", "humidity"]
            },
            constraint_template="{room}_{sensor}",
            generation_strategy="cartesian_product"
        )
        
        template.generate_all_instances()
        
        # Get all constraints for R1
        r1_constraints = template.get_instances_by_parameter("room", "R1")
        assert len(r1_constraints) == 2  # R1_temp, R1_humidity


class TestConstraintEvaluation:
    """Test evaluating all instances"""
    
    def test_evaluate_all_instances(self):
        """Evaluate entire template against observations"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={
                "sensor": ["temp", "humidity"],
                "min": 20,
                "max": 30
            },
            constraint_template="{sensor}: value >= {min} AND value <= {max}",
            generation_strategy="cartesian_product"
        )
        
        template.generate_all_instances()
        
        # Evaluate with valid values (both in range 20-30)
        observations = {"temp": 25, "humidity": 28}
        results = template.evaluate_all(observations)
        
        assert len(results) == 2
        assert all(r["status"] == "VALID" for r in results.values())
    
    def test_evaluate_with_violations(self):
        """Some constraints violated"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={
                "threshold": [10, 20, 30]
            },
            constraint_template="check_{threshold}: value < {threshold}",
            generation_strategy="cartesian_product"
        )
        
        template.generate_all_instances()
        
        observations = {"value": 15}
        results = template.evaluate_all(observations)
        
        # value=15 < 20 (VALID), < 30 (VALID), but NOT < 10 (VIOLATED)
        results_list = list(results.values())
        assert sum(1 for r in results_list if r["status"] == "VALID") == 2
        assert sum(1 for r in results_list if r["status"] == "VIOLATED") == 1


class TestRealWorldScenarios:
    """Test realistic domain scenarios"""
    
    def test_day4_iot_50_sensors_5_types(self):
        """Day 4: 50-room building with 5 sensor types"""
        rooms = [f"ROOM_{i:03d}" for i in range(50)]
        sensors = ["temp", "humidity", "co2", "light", "occupancy"]
        
        template = ParameterizedTemplate(
            name="building_sensor_check",
            parameter_set={
                "room": rooms,
                "sensor": sensors,
                "normal_min": 0,
                "normal_max": 100
            },
            constraint_template="{room}_{sensor}_bounds: "
                               "raw_reading >= {normal_min} AND raw_reading <= {normal_max}",
            generation_strategy="cartesian_product",
            severity="high"
        )
        
        count = template.generate_all_instances()
        assert count == 250  # 50 × 5
        
        metrics = template.get_metrics()
        assert metrics["instance_count"] == 250
        
        # Verify no manual definition needed
        instance = template.get_instance("ROOM_000_temp")
        assert "ROOM_000_temp_bounds" in instance["predicate"]
    
    def test_day5_gaming_1m_players_parameterized(self):
        """Day 5: 1M players (simulated with 100 for test)"""
        # In real scenario, would be 1M
        player_count = 100
        
        template = ParameterizedTemplate(
            name="player_skill_check",
            parameter_set={
                "player_id": [f"p{i}" for i in range(player_count)],
                "skill_min": 800,
                "skill_max": 2400
            },
            constraint_template="player_{player_id}_skill: "
                               "skill_rating >= {skill_min} AND skill_rating <= {skill_max}",
            generation_strategy="cartesian_product",
            severity="critical"
        )
        
        count = template.generate_all_instances()
        assert count == player_count
        
        # Can instantly get constraint for any player
        p50_constraint = template.get_instance("p50")
        assert "p50_skill" in p50_constraint["predicate"]
    
    def test_day2_finance_account_types(self):
        """Day 2: Account types × regions"""
        template = ParameterizedTemplate(
            name="account_risk_limits",
            parameter_set={
                "account_type": ["retail", "institutional", "vip"],
                "region": ["US", "EU", "APAC"],
                "max_leverage": 5
            },
            constraint_template="{account_type}_{region}_leverage: "
                               "leverage <= {max_leverage}",
            generation_strategy="cartesian_product"
        )
        
        count = template.generate_all_instances()
        assert count == 9  # 3 × 3
        
        # Can find all constraints for specific region
        us_constraints = template.get_instances_by_parameter("region", "US")
        assert len(us_constraints) == 3


class TestTemplateFactory:
    """Test factory methods"""
    
    def test_sensor_template_factory(self):
        """Factory creates sensor template"""
        template = TemplateFactory.create_sensor_template(
            sensor_types=["temp", "humidity"],
            locations=["R1", "R2"],
            threshold_ranges={"temp": (20, 25), "humidity": (30, 60)}
        )
        
        assert template.name == "sensor_bounds_check"
        assert "sensor_type" in template.parameter_set
        assert "location" in template.parameter_set
    
    def test_player_template_factory(self):
        """Factory creates gaming template"""
        template = TemplateFactory.create_player_template(
            player_count=1000,
            role_count=5
        )
        
        assert template.name == "player_skill_bounds"
        assert "role" in template.parameter_set
    
    def test_account_template_factory(self):
        """Factory creates finance template"""
        template = TemplateFactory.create_account_template(
            account_types=["retail", "institutional"],
            regions=["US", "EU"]
        )
        
        assert template.name == "account_risk_limits"
        assert len(template.parameter_set) >= 2


class TestMetrics:
    """Test metrics and diagnostics"""
    
    def test_metrics(self):
        """Template metrics"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={"a": [1, 2], "b": [3, 4]},
            constraint_template="",
            generation_strategy="cartesian_product",
            severity="critical"
        )
        
        template.generate_all_instances()
        
        metrics = template.get_metrics()
        assert metrics["name"] == "test"
        assert metrics["instance_count"] == 4
        assert metrics["parameter_count"] == 2
        assert metrics["severity"] == "critical"
        assert metrics["generation_strategy"] == "cartesian_product"
    
    def test_json_export(self):
        """Export template as JSON"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={"a": ["x", "y"]},
            constraint_template="test_{a}",
            generation_strategy="cartesian_product"
        )
        
        template.generate_all_instances()
        json_str = template.to_json()
        
        assert "test" in json_str
        assert "cartesian_product" in json_str


class TestReset:
    """Test reset functionality"""
    
    def test_reset_clears_instances(self):
        """Reset removes generated instances"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={"id": ["A", "B"]},
            constraint_template="{id}",
            generation_strategy="cartesian_product"
        )
        
        template.generate_all_instances()
        assert len(template.generated_constraints) == 2
        
        template.reset()
        assert len(template.generated_constraints) == 0
        assert template.instance_count == 0


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_parameter_list(self):
        """Parameter with empty list"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={"items": []},
            constraint_template="{items}",
            generation_strategy="cartesian_product"
        )
        
        count = template.generate_all_instances()
        assert count == 0
    
    def test_single_parameter(self):
        """Single parameter (not Cartesian)"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={"id": ["A", "B", "C"]},
            constraint_template="constraint_{id}",
            generation_strategy="cartesian_product"
        )
        
        count = template.generate_all_instances()
        assert count == 3
    
    def test_no_parameter_values(self):
        """Template with no parameters to substitute"""
        template = ParameterizedTemplate(
            name="test",
            parameter_set={},
            constraint_template="static_constraint: value < 100",
            generation_strategy="cartesian_product"
        )
        
        config = {}
        result = template._substitute_template(config)
        assert result == "static_constraint: value < 100"
