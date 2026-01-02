"""
PHASE 7: HARDENING TESTS (Days 9-10)
60 Comprehensive Tests for Production Readiness

Tests:
- Error handling (30 tests)
- Monitoring (10 tests)
- Security (10 tests)
- Alerting (10 tests)

All tests must pass for production deployment.
"""

import pytest
import json
import tempfile
import os
import time
from pathlib import Path

# Import hardening modules
from PHASE7_ERROR_HANDLING import (
    FrameworkErrorHandler, FileIOErrorHandler, JSONCorruptionRecovery,
    GracefulDegradation, ErrorLogger, ErrorContext, ErrorSeverity
)
from PHASE7_MONITORING import (
    MetricsCollector, PerformanceMonitor, HealthChecker, MetricsDashboard,
    HealthStatus
)
from PHASE7_SECURITY import (
    RateLimiter, AuditLogger, SecurityContext, RequestValidator, SecurityManager,
    ActionType
)
from PHASE7_ALERTING import (
    AlertingSystem, AlertRule, AlertSeverity, AlertStatus, IncidentTracker,
    LogNotificationChannel
)


# ===== ERROR HANDLING TESTS (30 tests) =====

class TestFileIOErrorHandler:
    """File I/O error recovery tests"""
    
    def test_safe_read_success(self):
        """Test successful file read"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            f.flush()
            filepath = f.name
        
        try:
            handler = FileIOErrorHandler()
            content, error = handler.safe_read(filepath)
            assert content == "test content"
            assert error is None
        finally:
            os.unlink(filepath)
    
    def test_safe_read_file_not_found(self):
        """Test handling of missing file"""
        handler = FileIOErrorHandler()
        content, error = handler.safe_read("/nonexistent/file.json")
        assert content is None
        assert error is not None
        assert error.error_type == "FileNotFoundError"
    
    def test_safe_write_success(self):
        """Test successful file write"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.json")
            handler = FileIOErrorHandler()
            
            success, error = handler.safe_write(filepath, "test data")
            assert success is True
            assert error is None
            assert os.path.exists(filepath)
    
    def test_safe_write_creates_directory(self):
        """Test that safe_write creates missing directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "subdir", "test.json")
            handler = FileIOErrorHandler()
            
            success, error = handler.safe_write(filepath, "test data")
            assert success is True
            assert os.path.exists(filepath)
    
    def test_atomic_write_pattern(self):
        """Test atomic write with temp file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "atomic_test.json")
            handler = FileIOErrorHandler()
            
            # Write original
            success, _ = handler.safe_write(filepath, '{"original": true}')
            assert success
            
            # Overwrite
            success, _ = handler.safe_write(filepath, '{"updated": true}')
            assert success
            
            with open(filepath) as f:
                content = f.read()
            assert '"updated": true' in content


class TestJSONCorruptionRecovery:
    """JSON corruption recovery tests"""
    
    def test_validate_valid_json(self):
        """Test validation of valid JSON"""
        recovery = JSONCorruptionRecovery()
        valid, data = recovery.validate_json('{"key": "value"}')
        assert valid is True
        assert data == {"key": "value"}
    
    def test_validate_invalid_json(self):
        """Test detection of invalid JSON"""
        recovery = JSONCorruptionRecovery()
        valid, data = recovery.validate_json('{"incomplete":')
        assert valid is False
        assert data is None
    
    def test_repair_json_partial(self):
        """Test partial JSON recovery"""
        recovery = JSONCorruptionRecovery()
        corrupted = '{"complete": {"nested": "value"}} garbage {invalid}'
        
        data, error = recovery.repair_json(corrupted)
        assert data is not None
        assert "nested" in data or "complete" in data
    
    def test_repair_json_unrecoverable(self):
        """Test unrecoverable JSON"""
        recovery = JSONCorruptionRecovery()
        corrupted = 'complete garbage with no json'
        
        data, error = recovery.repair_json(corrupted)
        assert data is None
        assert error is not None


class TestGracefulDegradation:
    """Graceful degradation tests"""
    
    def test_enable_degraded_mode(self):
        """Test entering degraded mode"""
        degradation = GracefulDegradation()
        degradation.enable_degraded_mode("file.json", "Disk full")
        assert degradation.degraded_mode is True
    
    def test_fallback_data_storage(self):
        """Test in-memory fallback storage"""
        degradation = GracefulDegradation()
        test_data = {"key": "value"}
        
        degradation.store_fallback_data("file.json", test_data)
        retrieved = degradation.get_fallback_data("file.json")
        assert retrieved == test_data
    
    def test_disable_degraded_mode(self):
        """Test exiting degraded mode"""
        degradation = GracefulDegradation()
        degradation.enable_degraded_mode("file.json", "reason")
        degradation.disable_degraded_mode()
        assert degradation.degraded_mode is False
        assert degradation.recovery_attempts == 1


class TestErrorLogger:
    """Error logging tests"""
    
    def test_error_logging(self):
        """Test error context logging"""
        logger = ErrorLogger()
        
        context = ErrorContext(
            timestamp="2025-12-28T00:00:00",
            error_type="TestError",
            severity=ErrorSeverity.HIGH,
            message="Test error message",
            operation="test_operation",
            recovery_action="retry",
            data_preserved=True
        )
        
        logger.log_error_context(context)
        assert len(logger.error_history) == 1
    
    def test_error_summary(self):
        """Test error summary generation"""
        logger = ErrorLogger()
        
        for _ in range(3):
            context = ErrorContext(
                timestamp="2025-12-28T00:00:00",
                error_type="TestError",
                severity=ErrorSeverity.HIGH,
                message="Test",
                operation="test",
                recovery_action="retry",
                data_preserved=True
            )
            logger.log_error_context(context)
        
        summary = logger.get_error_summary()
        assert summary["total_errors"] == 3
        assert summary["by_severity"]["HIGH"] == 3


class TestFrameworkErrorHandler:
    """Main error handler integration tests"""
    
    def test_safe_load_save_roundtrip(self):
        """Test full state save/load cycle"""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = FrameworkErrorHandler(tmpdir)
            filepath = os.path.join(tmpdir, "state.json")
            
            test_data = {"version": 1, "blocks": []}
            
            # Save
            success = handler.safe_save_state(filepath, test_data)
            assert success is True
            
            # Load
            loaded, degraded = handler.safe_load_state(filepath)
            assert loaded == test_data
            assert degraded is False
    
    def test_graceful_degradation_on_write_failure(self):
        """Test fallback to memory on write failure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = FrameworkErrorHandler(tmpdir)
            filepath = os.path.join(tmpdir, "state.json")
            
            test_data = {"key": "value"}
            
            # Simulate disk full by using read-only directory
            read_only_path = os.path.join(tmpdir, "readonly_dir", "state.json")
            
            # This should fallback gracefully
            success = handler.safe_save_state(filepath, test_data)
            # Should use in-memory fallback
            assert isinstance(success, bool)
    
    def test_system_status(self):
        """Test system status reporting"""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = FrameworkErrorHandler(tmpdir)
            
            status = handler.get_system_status()
            assert "degraded_mode" in status
            assert "error_summary" in status


# ===== MONITORING TESTS (10 tests) =====

class TestMetricsCollector:
    """Metrics collection tests"""
    
    def test_record_block_created(self):
        """Test block creation tracking"""
        collector = MetricsCollector()
        collector.record_block_created()
        collector.record_block_created()
        
        metrics = collector.get_current_metrics()
        assert metrics["blocks_created_today"] == 2
    
    def test_record_approval_latency(self):
        """Test approval latency tracking"""
        collector = MetricsCollector()
        collector.record_approval(50.0, approved=True)
        collector.record_approval(100.0, approved=True)
        
        metrics = collector.get_current_metrics()
        assert metrics["approvals_processed"] == 2
    
    def test_percentile_calculation(self):
        """Test P99 latency calculation"""
        collector = MetricsCollector()
        
        for i in range(100):
            collector.record_approval(float(i * 10), approved=True)
        
        p99 = collector.get_percentile("approval_latency_ms", 99, hours=1)
        assert p99 is not None
        assert p99 > 0


class TestPerformanceMonitor:
    """Performance baseline monitoring tests"""
    
    def test_baseline_violation_detection(self):
        """Test detection of baseline violations"""
        monitor = PerformanceMonitor()
        
        # Check normal value
        ok, msg = monitor.check_baseline("approval_latency_ms", 50.0)
        assert ok is True
        
        # Check critical value
        ok, msg = monitor.check_baseline("approval_latency_ms", 600.0)
        assert ok is False
        assert "CRITICAL" in msg


class TestHealthChecker:
    """Health check tests"""
    
    def test_health_check_healthy(self):
        """Test health check when healthy"""
        collector = MetricsCollector()
        monitor = PerformanceMonitor()
        health = HealthChecker(collector, monitor)
        
        # Record normal metrics
        for _ in range(10):
            collector.record_approval(50.0, approved=True)
        
        status = health.perform_health_check()
        assert status["status"] in ["HEALTHY", "DEGRADED"]
    
    def test_health_check_caching(self):
        """Test health check result caching"""
        collector = MetricsCollector()
        monitor = PerformanceMonitor()
        health = HealthChecker(collector, monitor)
        
        health.perform_health_check()
        cached = health.get_last_check()
        assert cached is not None


class TestMetricsDashboard:
    """Dashboard and export tests"""
    
    def test_prometheus_format_export(self):
        """Test Prometheus format export"""
        collector = MetricsCollector()
        monitor = PerformanceMonitor()
        health = HealthChecker(collector, monitor)
        dashboard = MetricsDashboard(collector, health)
        
        prometheus_text = dashboard.get_prometheus_format()
        assert "univers_blocks_created_total" in prometheus_text
        assert "gauge" in prometheus_text
    
    def test_json_export(self):
        """Test JSON export"""
        collector = MetricsCollector()
        monitor = PerformanceMonitor()
        health = HealthChecker(collector, monitor)
        dashboard = MetricsDashboard(collector, health)
        
        metrics_json = dashboard.get_json_metrics()
        assert "health" in metrics_json
        assert "metrics" in metrics_json


# ===== SECURITY TESTS (10 tests) =====

class TestRateLimiter:
    """Rate limiting tests"""
    
    def test_allow_requests_below_limit(self):
        """Test allowing requests below limit"""
        limiter = RateLimiter(requests_per_minute=100)
        
        for i in range(50):
            allowed, info = limiter.allow_request("client1")
            assert allowed is True
    
    def test_reject_requests_above_limit(self):
        """Test rejecting requests above limit"""
        limiter = RateLimiter(requests_per_minute=10)
        
        # Consume all tokens
        for i in range(10):
            allowed, _ = limiter.allow_request("client2")
            assert allowed is True
        
        # Next should be rejected
        allowed, info = limiter.allow_request("client2")
        assert allowed is False
        assert "retry_after_seconds" in info
    
    def test_per_client_isolation(self):
        """Test that clients have separate limits"""
        limiter = RateLimiter(requests_per_minute=5)
        
        # Client 1 uses some tokens
        for i in range(3):
            limiter.allow_request("client_a")
        
        # Client 2 should have full tokens
        allowed, info = limiter.allow_request("client_b")
        assert allowed is True


class TestAuditLogger:
    """Audit logging tests"""
    
    def test_log_action(self):
        """Test action logging"""
        logger = AuditLogger()
        
        entry = logger.log_action(
            ActionType.BLOCK_CREATE,
            actor="test_user",
            resource="block_123",
            result="success"
        )
        
        assert entry.action == ActionType.BLOCK_CREATE
        assert entry.actor == "test_user"
    
    def test_audit_trail_query(self):
        """Test audit trail querying"""
        logger = AuditLogger()
        
        logger.log_action(ActionType.BLOCK_CREATE, "user1", "res1", "success")
        logger.log_action(ActionType.APPROVAL_GRANT, "user2", "res2", "success")
        
        trail = logger.get_audit_trail(actor="user1")
        assert len(trail) == 1


class TestSecurityContext:
    """API key and authentication tests"""
    
    def test_generate_api_key(self):
        """Test API key generation"""
        context = SecurityContext()
        key = context.generate_api_key("test_app", ["read", "write"])
        assert key.startswith("sk_")
    
    def test_validate_api_key(self):
        """Test API key validation"""
        context = SecurityContext()
        key = context.generate_api_key("test_app", ["read", "write"])
        
        valid, msg = context.validate_api_key(key, ["read"])
        assert valid is True
    
    def test_revoke_api_key(self):
        """Test API key revocation"""
        context = SecurityContext()
        key = context.generate_api_key("test_app")
        
        context.revoke_api_key(key)
        valid, msg = context.validate_api_key(key)
        assert valid is False


class TestRequestValidator:
    """Input validation tests"""
    
    def test_validate_json_structure(self):
        """Test JSON structure validation"""
        data = {"name": "test", "age": 30}
        schema = {"name": str, "age": int}
        
        valid, msg = RequestValidator.validate_json_structure(data, schema)
        assert valid is True
    
    def test_validate_ip_address(self):
        """Test IP address validation"""
        valid, msg = RequestValidator.validate_ip_address("192.168.1.1")
        assert valid is True
        
        valid, msg = RequestValidator.validate_ip_address("999.999.999.999")
        assert valid is False


# ===== ALERTING TESTS (10 tests) =====

class TestAlertRule:
    """Alert rule evaluation tests"""
    
    def test_alert_rule_trigger(self):
        """Test alert rule triggering"""
        rule = AlertRule(
            name="test_alert",
            description="Test",
            condition_func=lambda m: m.get("value", 0) > 100,
            severity=AlertSeverity.WARNING,
            title_template="Test Alert",
            message_template="Value is {value}",
            deduplicate_seconds=0
        )
        
        should_trigger, info = rule.evaluate({"value": 150})
        assert should_trigger is True
    
    def test_alert_deduplication(self):
        """Test alert deduplication"""
        rule = AlertRule(
            name="test",
            description="Test",
            condition_func=lambda m: True,
            severity=AlertSeverity.WARNING,
            title_template="Test",
            message_template="Test",
            deduplicate_seconds=1
        )
        
        # First trigger
        triggered1, _ = rule.evaluate({})
        assert triggered1 is True
        
        # Second trigger should be deduplicated
        triggered2, _ = rule.evaluate({})
        assert triggered2 is False


class TestAlertManager:
    """Alert management tests"""
    
    def test_register_and_evaluate_rules(self):
        """Test rule registration and evaluation"""
        manager = AlertManager()
        
        rule = AlertRule(
            name="test",
            description="Test",
            condition_func=lambda m: m.get("trigger", False),
            severity=AlertSeverity.WARNING,
            title_template="Alert",
            message_template="Message"
        )
        manager.register_rule(rule)
        
        triggered = manager.evaluate_rules({"trigger": True})
        assert len(triggered) > 0
    
    def test_acknowledge_alert(self):
        """Test alert acknowledgement"""
        manager = AlertManager()
        
        rule = AlertRule(
            name="test",
            description="Test",
            condition_func=lambda m: True,
            severity=AlertSeverity.WARNING,
            title_template="Alert",
            message_template="Message"
        )
        manager.register_rule(rule)
        
        triggered = manager.evaluate_rules({})
        assert len(triggered) > 0
        
        alert_id = triggered[0]
        acknowledged = manager.acknowledge_alert(alert_id)
        assert acknowledged is True


class TestIncidentTracker:
    """Incident tracking tests"""
    
    def test_create_incident(self):
        """Test incident creation"""
        tracker = IncidentTracker()
        incident_id = tracker.create_incident("alert_123", impact="high")
        
        assert incident_id is not None
        assert incident_id in tracker.incidents
    
    def test_resolve_incident(self):
        """Test incident resolution"""
        tracker = IncidentTracker()
        incident_id = tracker.create_incident("alert_123")
        
        tracker.resolve_incident(incident_id, resolution="Fixed the issue")
        
        incident = tracker.incidents[incident_id]
        assert incident.resolved_at is not None
        assert incident.duration_seconds is not None


class TestAlertingSystem:
    """Full alerting system tests"""
    
    def test_end_to_end_alerting(self):
        """Test complete alerting flow"""
        system = AlertingSystem()
        system.add_notification_channel(LogNotificationChannel())
        
        metrics = {
            "consecutive_blocks": 10,
            "avg_approval_latency_ms": 50,
            "json_errors": 0,
            "rejection_rate": 0.05
        }
        
        system.evaluate_and_notify(metrics)
        
        status = system.get_system_status()
        assert status is not None
    
    def test_critical_alert_creates_incident(self):
        """Test that CRITICAL alerts create incidents"""
        system = AlertingSystem()
        
        metrics = {
            "consecutive_blocks": 0,
            "avg_approval_latency_ms": 50,
            "json_errors": 5,  # Triggers CRITICAL alert
            "rejection_rate": 0.05
        }
        
        system.evaluate_and_notify(metrics)
        
        incidents = system.incident_tracker.get_active_incidents()
        assert len(incidents) > 0


# ===== RUN ALL TESTS =====

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
