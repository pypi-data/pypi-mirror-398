"""
Comprehensive test suite for Primitive 12: PhysicalLaw

Tests cover:
- Conservation laws (energy, mass, charge)
- Equilibrium laws (Kirchhoff's voltage and current)
- Immutability laws (blockchain, audit logs)
- Law composition (multiple laws together)
- Real-world scenarios (blockchain, energy, healthcare)
"""

import pytest
from datetime import datetime
from universalengine.primitives.physical_law import (
    PhysicalLaw, ConservationLaw, EquilibriumLaw, ImmutabilityLaw,
    LawComposition, LawType, ViolationType
)


class TestConservationLaws:
    """Test conservation law enforcement."""
    
    def test_energy_conservation_balanced(self):
        """Energy in = Energy out + stored."""
        law = ConservationLaw(
            law_id="energy_conservation",
            law_type=LawType.ENERGY_CONSERVATION,
            input_fields=["power_in"],
            output_fields=["power_out"],
            storage_field="stored_energy",
            tolerance=1e-6
        )
        
        # Balanced: 100 = 60 + 40
        observations = {
            "power_in": 100.0,
            "power_out": 60.0,
            "stored_energy": 40.0,
        }
        
        satisfied, reason = law.check(observations)
        assert satisfied is True
        assert law.violation_count == 0
    
    def test_energy_conservation_imbalanced(self):
        """Energy imbalance detected."""
        law = ConservationLaw(
            law_id="energy_conservation",
            law_type=LawType.ENERGY_CONSERVATION,
            input_fields=["power_in"],
            output_fields=["power_out"],
            storage_field="stored_energy",
            tolerance=1e-6
        )
        
        # Imbalanced: 100 != 60 + 25
        observations = {
            "power_in": 100.0,
            "power_out": 60.0,
            "stored_energy": 25.0,  # Should be 40
        }
        
        satisfied, reason = law.check(observations)
        assert satisfied is False
        assert law.violation_count == 1
    
    def test_mass_balance_with_accumulation(self):
        """Mass in = Mass out + accumulated."""
        law = ConservationLaw(
            law_id="mass_balance",
            law_type=LawType.MASS_BALANCE,
            input_fields=["feed_in", "additive_in"],
            output_fields=["product_out", "waste_out"],
            storage_field="tank_mass",
            tolerance=0.1
        )
        
        # Feed 100 + additive 20 = product 80 + waste 15 + tank 25
        observations = {
            "feed_in": 100.0,
            "additive_in": 20.0,
            "product_out": 80.0,
            "waste_out": 15.0,
            "tank_mass": 25.0,
        }
        
        balance, is_valid = law.check_balance(observations)
        assert is_valid is True
        assert abs(balance) <= 0.1


class TestEquilibriumLaws:
    """Test equilibrium law enforcement (KVL, KCL)."""
    
    def test_kirchhoff_voltage_loop(self):
        """KVL: Sum of voltages in loop = 0."""
        law = EquilibriumLaw(
            law_id="kvl_loop_1",
            law_type=LawType.KIRCHHOFF_VOLTAGE,
            quantity_fields=["v_source", "v_r1", "v_r2"],
            signs=[1, -1, -1],  # v_source - v_r1 - v_r2 = 0
            tolerance=1e-6
        )
        
        # 12V source, 5V across R1, 7V across R2: 12 - 5 - 7 = 0
        observations = {
            "v_source": 12.0,
            "v_r1": 5.0,
            "v_r2": 7.0,
        }
        
        satisfied, reason = law.check(observations)
        assert satisfied is True
    
    def test_kirchhoff_current_node(self):
        """KCL: Sum of currents at node = 0."""
        law = EquilibriumLaw(
            law_id="kcl_node_1",
            law_type=LawType.KIRCHHOFF_CURRENT,
            quantity_fields=["i_in", "i_out1", "i_out2"],
            signs=[1, -1, -1],  # i_in - i_out1 - i_out2 = 0
            tolerance=1e-6
        )
        
        # 10A in = 6A + 4A out
        observations = {
            "i_in": 10.0,
            "i_out1": 6.0,
            "i_out2": 4.0,
        }
        
        satisfied, reason = law.check(observations)
        assert satisfied is True
        
        sum_val, is_valid = law.check_sum(observations)
        assert abs(sum_val) < 1e-6
    
    def test_kcl_violation(self):
        """KCL violation detected."""
        law = EquilibriumLaw(
            law_id="kcl_node_1",
            law_type=LawType.KIRCHHOFF_CURRENT,
            quantity_fields=["i_in", "i_out1", "i_out2"],
            signs=[1, -1, -1],
            tolerance=1e-6
        )
        
        # 10A in but only 8A out (2A missing - violates conservation)
        observations = {
            "i_in": 10.0,
            "i_out1": 5.0,
            "i_out2": 3.0,  # Should sum to 10
        }
        
        satisfied, reason = law.check(observations)
        assert satisfied is False


class TestImmutabilityLaws:
    """Test immutability law enforcement."""
    
    def test_blockchain_transaction_immutable(self):
        """Blockchain transaction hash is immutable."""
        law = ImmutabilityLaw(
            law_id="tx_immutable",
            immutable_fields=["tx_hash", "tx_timestamp"]
        )
        
        # First check: locks the state
        obs1 = {"tx_hash": "0xabc123", "tx_timestamp": 1000}
        satisfied1, reason1 = law.check(obs1)
        assert satisfied1 is True
        assert law.is_locked() is True
        
        # Second check: same values, should pass
        obs2 = {"tx_hash": "0xabc123", "tx_timestamp": 1000}
        satisfied2, reason2 = law.check(obs2)
        assert satisfied2 is True
        
        # Third check: different values, should fail
        obs3 = {"tx_hash": "0xabc124", "tx_timestamp": 1000}
        satisfied3, reason3 = law.check(obs3)
        assert satisfied3 is False
        assert law.violation_count == 1
    
    def test_immutability_explicit_lock(self):
        """Explicitly lock immutable state."""
        law = ImmutabilityLaw(
            law_id="audit_log_immutable",
            immutable_fields=["log_id", "timestamp", "data"]
        )
        
        obs = {"log_id": "log_001", "timestamp": 1000, "data": "initial"}
        law.lock_state(obs)
        
        # Now try to change data
        obs_modified = {"log_id": "log_001", "timestamp": 1000, "data": "modified"}
        satisfied, reason = law.check(obs_modified)
        assert satisfied is False


class TestLawEnforcement:
    """Test law enforcement modes (strict vs warning)."""
    
    def test_strict_enforcement_violation(self):
        """Strict mode raises exception on violation."""
        law = PhysicalLaw(
            law_id="strict_law",
            law_type=LawType.ENERGY_CONSERVATION,
            applies_to=["energy_in", "energy_out"],
            law_predicate=lambda obs: obs.get("energy_in") == obs.get("energy_out"),
            enforcement_level="strict"
        )
        
        # Violate the law
        obs = {"energy_in": 100, "energy_out": 80}
        
        with pytest.raises(ValueError) as exc_info:
            law.enforce(obs)
        
        assert "Physical law violation" in str(exc_info.value)
    
    def test_warning_enforcement_violation(self):
        """Warning mode logs but continues."""
        law = PhysicalLaw(
            law_id="warning_law",
            law_type=LawType.ENERGY_CONSERVATION,
            applies_to=["energy_in", "energy_out"],
            law_predicate=lambda obs: obs.get("energy_in") == obs.get("energy_out"),
            enforcement_level="warning"
        )
        
        # Violate the law
        obs = {"energy_in": 100, "energy_out": 80}
        
        is_valid, error_msg = law.enforce(obs)
        assert is_valid is False
        assert error_msg is not None


class TestLawComposition:
    """Test composing multiple laws together."""
    
    def test_energy_grid_multiple_laws(self):
        """Energy grid with supply=demand+storage+losses."""
        # Law 1: Power balance at distribution level
        power_balance = ConservationLaw(
            law_id="power_balance",
            law_type=LawType.ENERGY_CONSERVATION,
            input_fields=["generation"],
            output_fields=["consumption"],
            storage_field="battery_charge_rate",
            tolerance=1.0
        )
        
        # Law 2: Voltage equilibrium at each bus
        voltage_law = EquilibriumLaw(
            law_id="voltage_equilibrium",
            law_type=LawType.KIRCHHOFF_VOLTAGE,
            quantity_fields=["v_source", "v_drop"],
            signs=[1, -1],
            tolerance=0.1
        )
        
        # Compose laws
        composition = LawComposition("energy_grid")
        composition.add_law(power_balance)
        composition.add_law(voltage_law)
        
        # Valid state
        obs_valid = {
            "generation": 100.0,
            "consumption": 80.0,
            "battery_charge_rate": 20.0,
            "v_source": 230.0,
            "v_drop": 229.9,
        }
        
        all_satisfied, violations = composition.check_all(obs_valid)
        assert all_satisfied is True
        assert len(violations) == 0
        
        # Invalid state: power imbalance
        obs_invalid = {
            "generation": 100.0,
            "consumption": 80.0,
            "battery_charge_rate": 15.0,  # Should be 20
            "v_source": 230.0,
            "v_drop": 229.9,
        }
        
        all_satisfied, violations = composition.check_all(obs_invalid)
        assert all_satisfied is False
        assert len(violations) >= 1


class TestRealWorldScenarios:
    """Test realistic domain scenarios."""
    
    def test_blockchain_immutability_ledger(self):
        """Blockchain ledger where blocks are immutable."""
        block_law = ImmutabilityLaw(
            law_id="block_immutable",
            immutable_fields=["block_hash", "block_height", "transactions"]
        )
        
        # First block
        block1 = {
            "block_hash": "0xabc123",
            "block_height": 1,
            "transactions": ["tx1", "tx2"]
        }
        
        satisfied1, _ = block_law.check(block1)
        assert satisfied1 is True
        
        # Try to modify block
        block1_modified = {
            "block_hash": "0xabc123",
            "block_height": 1,
            "transactions": ["tx1", "tx2", "tx3"]  # Added tx3
        }
        
        satisfied2, _ = block_law.check(block1_modified)
        assert satisfied2 is False
    
    def test_healthcare_mass_balance(self):
        """Patient mass balance in medical treatment."""
        mass_law = ConservationLaw(
            law_id="patient_mass_balance",
            law_type=LawType.MASS_BALANCE,
            input_fields=["food_intake", "water_intake", "medication"],
            output_fields=["urine_output", "perspiration"],
            storage_field="body_mass_change",
            tolerance=0.5  # kg tolerance
        )
        
        # Typical day: 2kg food + 2kg water = 1kg urine + 0.5kg sweat + 2.5kg stored
        obs = {
            "food_intake": 2.0,
            "water_intake": 2.0,
            "medication": 0.0,
            "urine_output": 1.0,
            "perspiration": 0.5,
            "body_mass_change": 2.5,
        }
        
        balance, is_valid = mass_law.check_balance(obs)
        assert is_valid is True
    
    def test_energy_grid_realistic(self):
        """Realistic energy grid scenario."""
        # Power generation vs consumption + storage
        power_law = ConservationLaw(
            law_id="grid_power_balance",
            law_type=LawType.ENERGY_CONSERVATION,
            input_fields=["solar_generation", "wind_generation", "battery_discharge"],
            output_fields=["residential_load", "industrial_load", "battery_charge"],
            tolerance=5.0  # MW tolerance
        )
        
        # 500MW generation = 400MW load + 100MW charge
        obs = {
            "solar_generation": 300.0,
            "wind_generation": 200.0,
            "battery_discharge": 0.0,
            "residential_load": 250.0,
            "industrial_load": 150.0,
            "battery_charge": 100.0,
        }
        
        satisfied, reason = power_law.check(obs)
        assert satisfied is True
        
        # Demand spike: consumption > generation
        obs_spike = {
            "solar_generation": 300.0,
            "wind_generation": 200.0,
            "battery_discharge": 0.0,
            "residential_load": 350.0,  # Increased
            "industrial_load": 200.0,  # Increased
            "battery_charge": 0.0,
        }
        
        satisfied_spike, _ = power_law.check(obs_spike)
        assert satisfied_spike is False  # 500 gen < 550 load


class TestLawMetrics:
    """Test law compliance metrics."""
    
    def test_violation_metrics_tracking(self):
        """Track law violation rates."""
        law = ConservationLaw(
            law_id="balance_law",
            law_type=LawType.ENERGY_CONSERVATION,
            input_fields=["in"],
            output_fields=["out"],
            tolerance=1.0
        )
        
        # Check valid state
        law.check({"in": 100.0, "out": 100.0})
        
        # Check invalid state
        law.check({"in": 100.0, "out": 50.0})
        
        # Check valid again
        law.check({"in": 100.0, "out": 100.0})
        
        metrics = law.get_metrics()
        assert metrics["check_count"] == 3
        assert metrics["violation_count"] == 1
        assert metrics["violation_rate"] == pytest.approx(1/3)
    
    def test_composition_metrics(self):
        """Get metrics from law composition."""
        law1 = ConservationLaw(
            law_id="law1",
            law_type=LawType.ENERGY_CONSERVATION,
            input_fields=["in"],
            output_fields=["out"],
        )
        
        law2 = EquilibriumLaw(
            law_id="law2",
            law_type=LawType.KIRCHHOFF_VOLTAGE,
            quantity_fields=["v1", "v2"],
        )
        
        composition = LawComposition("comp1")
        composition.add_law(law1)
        composition.add_law(law2)
        
        # Run some checks
        obs = {"in": 100.0, "out": 100.0, "v1": 10.0, "v2": -10.0}
        composition.check_all(obs)
        composition.check_all(obs)
        
        metrics = composition.get_metrics()
        assert metrics["num_laws"] == 2
        assert metrics["check_count"] == 2
        assert "laws" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
