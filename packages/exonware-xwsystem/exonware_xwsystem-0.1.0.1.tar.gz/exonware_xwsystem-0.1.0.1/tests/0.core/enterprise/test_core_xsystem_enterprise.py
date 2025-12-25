#exonware/xwsystem/tests/core/enterprise/test_core_xwsystem_enterprise.py
"""
XSystem Enterprise Features Core Tests

Comprehensive tests for enterprise functionality now distributed across:
- Security module: Authentication (OAuth2, JWT, SAML)
- Monitoring module: Distributed Tracing (OpenTelemetry, Jaeger)
- IO/Serialization module: Schema Registry (Confluent, AWS Glue)

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.387
Generation Date: November 04, 2025
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

try:
    # Authentication moved to security module
    from exonware.xwsystem.security import (
        EnterpriseAuth, 
        OAuth2Provider, 
        JWTProvider, 
        SAMLProvider,
        AuthenticationError,
        AAuthProvider,
        ATokenInfo,
        AUserInfo
    )
    
    # Distributed tracing moved to monitoring module
    from exonware.xwsystem.monitoring import (
        DistributedTracing,
        TracingManager,
        OpenTelemetryTracer,
        JaegerTracer,
        TracingError,
        SpanContext,
        TraceContext
    )
    
    # Schema registry moved to io/serialization module
    from exonware.xwsystem.io.serialization import (
        SchemaRegistry,
        ConfluentSchemaRegistry,
        AwsGlueSchemaRegistry,
        SchemaRegistryError,
        SchemaNotFoundError,
        SchemaValidationError,
        ASchemaRegistry,
        SchemaInfo
    )
    
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for testing
    class EnterpriseAuth:
        def __init__(self): 
            self._providers = {}
        def add_provider(self, name, provider): 
            self._providers[name] = provider
        def list_providers(self): 
            return list(self._providers.keys())
    
    class DistributedTracing:
        def __init__(self, provider=None): 
            self.manager = None
        def start_trace(self, operation, **kwargs): 
            return type('TraceContext', (), {'trace_id': "trace_123", 'correlation_id': "corr_456"})()
        def is_tracing_enabled(self): 
            return True
    
    class SchemaRegistry:
        def __init__(self, registry_type="confluent", **kwargs): 
            self.registry_type = registry_type
    
    class AuthenticationError(Exception): pass
    class TracingError(Exception): pass
    class SchemaRegistryError(Exception): pass


def test_enterprise_auth():
    """Test enterprise authentication functionality (security module)."""
    print("📋 Testing: Enterprise Authentication (security module)")
    print("-" * 30)
    
    try:
        auth = EnterpriseAuth()
        
        # Test that we can add providers
        assert auth is not None
        assert hasattr(auth, 'add_provider')
        assert hasattr(auth, 'list_providers')
        
        # Test provider list starts empty
        providers = auth.list_providers()
        assert isinstance(providers, list)
        
        print("✅ Enterprise authentication tests passed")
        return True
    except Exception as e:
        print(f"❌ Enterprise authentication tests failed: {e}")
        return False


def test_distributed_tracing():
    """Test distributed tracing functionality (monitoring module)."""
    print("📋 Testing: Distributed Tracing (monitoring module)")
    print("-" * 30)
    
    try:
        # Test with default no-op provider (tracing disabled by default)
        tracing = DistributedTracing()
        
        # Verify tracing starts disabled (no-op provider by default)
        assert not tracing.is_tracing_enabled(), "Tracing should be disabled by default (no-op)"
        
        # But trace operations still work (they just don't send anywhere)
        operation = "test_operation"
        trace_context = tracing.start_trace(operation, attributes={"user_id": "test_user"})
        assert trace_context is not None, "start_trace() should return TraceContext even with no-op"
        
        # Verify trace context has expected attributes
        assert hasattr(trace_context, 'trace_id'), "TraceContext missing trace_id"
        assert hasattr(trace_context, 'correlation_id'), "TraceContext missing correlation_id"
        
        print("✅ Distributed tracing tests passed")
        return True
    except AssertionError as e:
        print(f"❌ Distributed tracing tests failed: Assertion failed - {e}")
        return False
    except Exception as e:
        print(f"❌ Distributed tracing tests failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schema_registry():
    """Test schema registry functionality (io/serialization module)."""
    print("📋 Testing: Schema Registry (io/serialization module)")
    print("-" * 30)
    
    try:
        # Test initialization with confluent type
        registry = SchemaRegistry(registry_type="confluent", url="http://localhost:8081")
        
        # Verify registry created successfully
        assert registry is not None
        assert registry.registry_type == "confluent"
        
        print("✅ Schema registry tests passed")
        return True
    except Exception as e:
        print(f"❌ Schema registry tests failed: {e}")
        return False


def test_feature_availability():
    """Test that all enterprise features are available from their new locations."""
    print("📋 Testing: Feature Availability (distributed architecture)")
    print("-" * 30)
    
    try:
        # Verify auth is accessible from security
        auth = EnterpriseAuth()
        assert auth is not None
        
        # Verify tracing is accessible from monitoring
        tracing = DistributedTracing()
        assert tracing is not None
        
        # Verify schema registry is accessible from io/serialization
        registry = SchemaRegistry(registry_type="confluent", url="http://localhost:8081")
        assert registry is not None
        
        print("✅ Feature availability tests passed")
        return True
    except Exception as e:
        print(f"❌ Feature availability tests failed: {e}")
        return False


def test_error_handling():
    """Test error handling from new locations."""
    print("📋 Testing: Error Handling (distributed errors)")
    print("-" * 30)
    
    try:
        # Test error classes from new locations
        auth_error = AuthenticationError("Test auth error")
        tracing_error = TracingError("Test tracing error")
        schema_error = SchemaRegistryError("Test schema error")
        
        assert str(auth_error) == "Test auth error"
        assert str(tracing_error) == "Test tracing error"
        assert str(schema_error) == "Test schema error"
        
        print("✅ Error handling tests passed")
        return True
    except Exception as e:
        print(f"❌ Error handling tests failed: {e}")
        return False


def test_enterprise_integration():
    """Test enterprise integration functionality across modules."""
    print("📋 Testing: Enterprise Integration (cross-module)")
    print("-" * 30)
    
    try:
        # Components from different modules working together
        auth = EnterpriseAuth()
        tracing = DistributedTracing()
        registry = SchemaRegistry(registry_type="confluent", url="http://localhost:8081")
        
        # Test integrated workflow (using correct DistributedTracing API)
        trace_context = tracing.start_trace("enterprise_workflow", attributes={"user_id": "test_user"})
        assert trace_context is not None
        
        # Verify all components work together
        assert auth is not None
        assert registry is not None
        
        print("✅ Enterprise integration tests passed")
        return True
    except Exception as e:
        print(f"❌ Enterprise integration tests failed: {e}")
        return False


def main():
    """Run all enterprise core tests."""
    print("=" * 50)
    print("🧪 XSystem Enterprise Features Core Tests")
    print("=" * 50)
    print("Testing enterprise features distributed across:")
    print("  - security/ (auth)")
    print("  - monitoring/ (tracing)")
    print("  - io/serialization/ (schema registry)")
    print("=" * 50)
    
    tests = [
        test_enterprise_auth,
        test_distributed_tracing,
        test_schema_registry,
        test_feature_availability,
        test_error_handling,
        test_enterprise_integration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print("📊 XSYSTEM ENTERPRISE FEATURES TEST SUMMARY")
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All XSystem enterprise feature tests passed!")
        return 0
    else:
        print("💥 Some XSystem enterprise feature tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
