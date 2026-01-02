"""
Unit tests for DistributedVariable primitive

Tests cover:
- All aggregation modes (consensus_threshold, majority, unanimous, quorum, eventual)
- Byzantine fault tolerance
- Instance tracking
- Real-world scenarios (BGP, Blockchain, IoT, Gaming)
"""

import pytest
from universalengine.primitives.distributed_variable import (
    DistributedVariable,
    AggregationMode,
    ConsistencyModel
)


class TestConsensusThreshold:
    """Test Byzantine consensus (default 2/3 tolerance)"""
    
    def test_2_of_3_consensus(self):
        """2 out of 3 validators agree -> CONSENSUS"""
        dv = DistributedVariable(
            name="test",
            instances=[
                {"id": "v1"},
                {"id": "v2"},
                {"id": "v3"}
            ],
            aggregation_mode="consensus_threshold",
            threshold=0.66  # 2/3 = 0.666... < 0.67, so use 0.66
        )
        
        dv.add_observation("v1", True, 1000)
        dv.add_observation("v2", True, 1001)
        dv.add_observation("v3", False, 1002)
        
        result = dv.aggregate_value()
        assert result["status"] == "CONSENSUS"
        assert result["value"] == True
        assert result["agreement"] >= 0.66
    
    def test_consensus_failure(self):
        """Less than threshold agreement -> NO_CONSENSUS"""
        dv = DistributedVariable(
            name="test",
            instances=[
                {"id": "v1"},
                {"id": "v2"},
                {"id": "v3"}
            ],
            aggregation_mode="consensus_threshold",
            threshold=0.67
        )
        
        # Split vote: 1 True, 2 False
        dv.add_observation("v1", True, 1000)
        dv.add_observation("v2", False, 1001)
        dv.add_observation("v3", False, 1002)
        
        result = dv.aggregate_value()
        assert result["status"] == "NO_CONSENSUS"
        assert result["value"] is None
    
    def test_higher_threshold(self):
        """Custom threshold (90%)"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": f"n{i}"} for i in range(10)],
            aggregation_mode="consensus_threshold",
            threshold=0.90
        )
        
        # 9 out of 10 agree (90%) -> CONSENSUS at exactly threshold
        for i in range(9):
            dv.add_observation(f"n{i}", "A", 1000 + i)
        dv.add_observation("n9", "B", 1009)
        
        result = dv.aggregate_value()
        assert result["status"] == "CONSENSUS"


class TestMajority:
    """Test simple majority (>50%)"""
    
    def test_majority_wins(self):
        """3 out of 5 vote for A -> CONSENSUS"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": f"node{i}"} for i in range(5)],
            aggregation_mode="majority"
        )
        
        dv.add_observation("node0", "A", 1000)
        dv.add_observation("node1", "A", 1001)
        dv.add_observation("node2", "A", 1002)
        dv.add_observation("node3", "B", 1003)
        dv.add_observation("node4", "B", 1004)
        
        result = dv.aggregate_value()
        assert result["status"] == "CONSENSUS"
        assert result["value"] == "A"
        assert result["agreement"] == 0.6
    
    def test_no_majority(self):
        """Exactly 50% -> NO_CONSENSUS (need >50%)"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": f"node{i}"} for i in range(4)],
            aggregation_mode="majority"
        )
        
        dv.add_observation("node0", "A", 1000)
        dv.add_observation("node1", "A", 1001)
        dv.add_observation("node2", "B", 1002)
        dv.add_observation("node3", "B", 1003)
        
        result = dv.aggregate_value()
        assert result["status"] == "NO_CONSENSUS"


class TestUnanimous:
    """Test unanimous voting (100%)"""
    
    def test_unanimous_agreement(self):
        """All instances report same value -> CONSENSUS"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": f"s{i}"} for i in range(5)],
            aggregation_mode="unanimous"
        )
        
        for i in range(5):
            dv.add_observation(f"s{i}", 42, 1000 + i)
        
        result = dv.aggregate_value()
        assert result["status"] == "CONSENSUS"
        assert result["value"] == 42
        assert result["agreement"] == 1.0
    
    def test_unanimous_failure(self):
        """Any divergence -> NO_CONSENSUS"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": f"s{i}"} for i in range(3)],
            aggregation_mode="unanimous"
        )
        
        dv.add_observation("s0", True, 1000)
        dv.add_observation("s1", True, 1001)
        dv.add_observation("s2", False, 1002)  # One disagrees
        
        result = dv.aggregate_value()
        assert result["status"] == "NO_CONSENSUS"


class TestQuorum:
    """Test quorum-based consensus"""
    
    def test_quorum_members(self):
        """Only quorum members' votes count"""
        dv = DistributedVariable(
            name="test",
            instances=[
                {"id": "q1", "quorum": True},
                {"id": "q2", "quorum": True},
                {"id": "q3", "quorum": True},
                {"id": "observer1", "quorum": False}
            ],
            aggregation_mode="quorum"
        )
        
        # 2/3 quorum members agree (observer doesn't matter)
        dv.add_observation("q1", "YES", 1000)
        dv.add_observation("q2", "YES", 1001)
        dv.add_observation("q3", "NO", 1002)
        dv.add_observation("observer1", "YES", 1003)  # Doesn't affect quorum
        
        result = dv.aggregate_value()
        assert result["status"] == "CONSENSUS"
        assert result["value"] == "YES"


class TestEventual:
    """Test eventual consistency (last-write-wins)"""
    
    def test_eventual_converges(self):
        """Returns latest value, shows convergence progress"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": f"db{i}"} for i in range(5)],
            aggregation_mode="eventual"
        )
        
        # All write value "A" at t=1000
        for i in range(5):
            dv.add_observation(f"db{i}", "A", 1000)
        
        result = dv.aggregate_value()
        assert result["status"] == "EVENTUAL_CONSENSUS"
        assert result["value"] == "A"
        assert result["agreement"] == 1.0  # All have same value
    
    def test_eventual_propagation(self):
        """Partial propagation of new value"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": f"db{i}"} for i in range(5)],
            aggregation_mode="eventual"
        )
        
        # 3 old values, 2 new values
        dv.add_observation("db0", "A", 1000)
        dv.add_observation("db1", "A", 1000)
        dv.add_observation("db2", "A", 1000)
        dv.add_observation("db3", "B", 1100)  # New value
        dv.add_observation("db4", "B", 1100)  # New value
        
        result = dv.aggregate_value()
        assert result["status"] == "EVENTUAL_CONSENSUS"
        assert result["value"] == "B"  # Latest write
        assert result["agreement"] == 0.4  # 2/5 converged


class TestObservationTracking:
    """Test observation recording and tracking"""
    
    def test_add_observation(self):
        """Record observation from instance"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": "node1"}],
            aggregation_mode="majority"
        )
        
        dv.add_observation("node1", "value", 1234.5)
        
        assert dv.get_instance_value("node1") == "value"
        assert dv.get_instance_timestamp("node1") == 1234.5
    
    def test_unknown_instance(self):
        """Reject observations from unknown instances"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": "node1"}],
            aggregation_mode="majority"
        )
        
        with pytest.raises(ValueError):
            dv.add_observation("unknown_node", "value", 1000)
    
    def test_multiple_observations(self):
        """Multiple observations from same instance (latest wins)"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": "node1"}],
            aggregation_mode="majority"
        )
        
        dv.add_observation("node1", "old", 1000)
        dv.add_observation("node1", "new", 2000)
        
        assert dv.get_instance_value("node1") == "new"
        assert dv.get_instance_timestamp("node1") == 2000


class TestRealWorldScenarios:
    """Test realistic domain scenarios"""
    
    def test_day1_bgp_router_state(self):
        """Day 1: Each BGP router sees different neighbor state"""
        dv = DistributedVariable(
            name="bgp_neighbor_validity",
            instances=[
                {"id": "router_US_East"},
                {"id": "router_US_West"},
                {"id": "router_EU"}
            ],
            aggregation_mode="majority"
        )
        
        # 2/3 routers report neighbor valid
        dv.add_observation("router_US_East", True, 1000)
        dv.add_observation("router_US_West", True, 1001)
        dv.add_observation("router_EU", False, 1002)
        
        result = dv.aggregate_value()
        assert result["status"] == "CONSENSUS"
        assert result["value"] == True
    
    def test_day4_iot_sensor_consensus(self):
        """Day 4: 50 sensors, want majority to agree on comfort"""
        dv = DistributedVariable(
            name="building_comfort",
            instances=[{"id": f"sensor_{i:03d}"} for i in range(50)],
            aggregation_mode="majority"
        )
        
        # 35/50 sensors say comfortable (70%)
        for i in range(35):
            dv.add_observation(f"sensor_{i:03d}", "comfortable", 1000 + i)
        
        for i in range(35, 50):
            dv.add_observation(f"sensor_{i:03d}", "too_hot", 1000 + i)
        
        result = dv.aggregate_value()
        assert result["status"] == "CONSENSUS"
        assert result["value"] == "comfortable"
        assert result["agreement"] == 0.7
    
    def test_day5_gaming_server_coordination(self):
        """Day 5: Multiple game servers track same match state"""
        dv = DistributedVariable(
            name="match_state",
            instances=[
                {"id": "game_server_1"},
                {"id": "game_server_2"},
                {"id": "game_server_3"}
            ],
            aggregation_mode="consensus_threshold",
            threshold=0.66  # 2/3 = 0.666..., use 0.66
        )
        
        # 2/3 servers have same match state
        dv.add_observation("game_server_1", "PLAYER_1_WINS", 2000.1)
        dv.add_observation("game_server_2", "PLAYER_1_WINS", 2000.2)
        dv.add_observation("game_server_3", "PLAYER_2_WINS", 2000.5)  # Lagged
        
        result = dv.aggregate_value()
        assert result["status"] == "CONSENSUS"
        assert result["value"] == "PLAYER_1_WINS"
    
    def test_day6_blockchain_validator_voting(self):
        """Day 6: 10 validators vote on block validity (2/3 Byzantine tolerance)"""
        dv = DistributedVariable(
            name="block_validity",
            instances=[{"id": f"validator_{i:02d}"} for i in range(10)],
            aggregation_mode="consensus_threshold",
            threshold=0.67  # 2/3 = 6.67 (so 7+)
        )
        
        # 7 validators say valid, 3 say invalid (70% > 67%)
        for i in range(7):
            dv.add_observation(f"validator_{i:02d}", "VALID", 5000 + i)
        
        for i in range(7, 10):
            dv.add_observation(f"validator_{i:02d}", "INVALID", 5000 + i)
        
        result = dv.aggregate_value()
        assert result["status"] == "CONSENSUS"
        assert result["value"] == "VALID"
        assert result["agreement"] >= 0.67


class TestMetrics:
    """Test internal metrics"""
    
    def test_metrics_tracking(self):
        """Track aggregation attempts and consensus rate"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": f"n{i}"} for i in range(3)],
            aggregation_mode="majority"
        )
        
        # First aggregation: no consensus (empty)
        dv.aggregate_value()
        
        # Add majority votes
        dv.add_observation("n0", "A", 1000)
        dv.add_observation("n1", "A", 1001)
        dv.add_observation("n2", "B", 1002)
        
        # Second aggregation: consensus
        dv.aggregate_value()
        
        metrics = dv.get_metrics()
        assert metrics["aggregation_count"] == 2
        assert metrics["consensus_rate"] == 0.5  # 1 consensus out of 2
    
    def test_metrics_responding_instances(self):
        """Track which instances are responding"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": f"n{i}"} for i in range(5)],
            aggregation_mode="majority"
        )
        
        # Only 3 out of 5 respond
        dv.add_observation("n0", "val", 1000)
        dv.add_observation("n1", "val", 1001)
        dv.add_observation("n2", "val", 1002)
        
        result = dv.aggregate_value()
        assert result["instances_responding"] == 3
        assert result["instances_total"] == 5


class TestInstanceHealth:
    """Test instance health checking"""
    
    def test_stale_instances(self):
        """Find instances not reporting recently"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": f"node{i}"} for i in range(3)],
            aggregation_mode="majority"
        )
        
        import time
        current_time = time.time()
        dv.add_observation("node0", "val", current_time - 200)  # Very old
        dv.add_observation("node1", "val2", current_time)  # Recent
        
        # This will test relative times
        stale = dv.get_stale_instances(max_age_seconds=100)
        # node0 is definitely old (200s ago), node2 has never reported
        assert "node0" in stale or "node2" in stale


class TestReset:
    """Test reset functionality"""
    
    def test_reset_clears_state(self):
        """Reset removes all observations and metrics"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": "n1"}],
            aggregation_mode="majority"
        )
        
        dv.add_observation("n1", "value", 1000)
        dv.aggregate_value()
        
        dv.reset()
        
        assert dv.get_instance_value("n1") is None
        assert dv.observation_count == 0
        assert len(dv.aggregation_history) == 0


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_observations(self):
        """No observations yet"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": "n1"}],
            aggregation_mode="majority"
        )
        
        result = dv.aggregate_value()
        assert result["status"] == "NO_CONSENSUS"
        assert result["value"] is None
        assert result["instances_responding"] == 0
    
    def test_single_instance(self):
        """Single instance always has consensus"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": "single"}],
            aggregation_mode="majority"
        )
        
        dv.add_observation("single", "only_value", 1000)
        result = dv.aggregate_value()
        
        assert result["status"] == "CONSENSUS"
        assert result["value"] == "only_value"
        assert result["agreement"] == 1.0
    
    def test_various_value_types(self):
        """Values can be strings, bools, numbers, etc"""
        dv = DistributedVariable(
            name="test",
            instances=[{"id": f"n{i}"} for i in range(3)],
            aggregation_mode="majority"
        )
        
        dv.add_observation("n0", True, 1000)
        dv.add_observation("n1", True, 1001)
        dv.add_observation("n2", False, 1002)
        
        result = dv.aggregate_value()
        assert result["value"] == True
        
        # Reset and try numbers
        dv.reset()
        dv.add_observation("n0", 42, 1000)
        dv.add_observation("n1", 42, 1001)
        dv.add_observation("n2", 99, 1002)
        
        result = dv.aggregate_value()
        assert result["value"] == 42
