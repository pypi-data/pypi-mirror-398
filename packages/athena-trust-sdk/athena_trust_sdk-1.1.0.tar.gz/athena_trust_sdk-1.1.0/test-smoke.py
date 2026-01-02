#!/usr/bin/env python3
"""
Basic smoke test for ATHENA Python SDK
Tests import, initialization, and basic error handling
"""

import sys

def test_imports():
    """Test that all main exports can be imported"""
    print("✓ Testing imports...")
    
    from athena import (
        Athena,
        AsyncAthena,
        AthenaError,
        AuthenticationError,
        RateLimitError,
        ValidationError,
        NotFoundError,
        verify_webhook_signature,
        parse_webhook,
        __version__
    )
    
    assert Athena is not None
    assert AsyncAthena is not None
    assert __version__ == "1.0.0"
    print(f"  SDK version: {__version__}")


def test_client_initialization():
    """Test client initialization"""
    print("✓ Testing client initialization...")
    
    from athena import Athena, AuthenticationError
    
    # Should fail without API key
    try:
        Athena(api_key="")
        assert False, "Should have raised AuthenticationError"
    except AuthenticationError:
        pass
    
    # Should succeed with API key
    client = Athena(api_key="test_key")
    assert client._api_key == "test_key"
    assert client._base_url == "https://api.athena.ai"
    
    # Check resources
    assert client.calibrate is not None
    assert client.bias is not None
    assert client.trust_score is not None
    assert client.audit is not None
    assert client.webhooks is not None
    assert client.export is not None
    assert client.stats is not None
    assert client.users is not None
    assert client.engines is not None
    
    client.close()


def test_async_client_initialization():
    """Test async client initialization"""
    print("✓ Testing async client initialization...")
    
    from athena import AsyncAthena, AuthenticationError
    
    # Should fail without API key
    try:
        AsyncAthena(api_key="")
        assert False, "Should have raised AuthenticationError"
    except AuthenticationError:
        pass
    
    # Should succeed with API key
    client = AsyncAthena(api_key="test_key")
    assert client._api_key == "test_key"
    assert client._base_url == "https://api.athena.ai"
    
    # Check resources
    assert client.calibrate is not None
    assert client.bias is not None
    assert client.trust_score is not None


def test_models():
    """Test Pydantic models"""
    print("✓ Testing Pydantic models...")
    
    from athena.models import (
        CalibrateResponse,
        DetectBiasResponse,
        TrustScoreResponse,
        AuditTrailResponse,
        Webhook,
        StatsResponse
    )
    
    # Test snake_case to camelCase aliasing
    from pydantic import ValidationError
    
    try:
        # Should accept camelCase
        stats = StatsResponse.model_validate({
            "totalDecisions": 100,
            "biasIncidents": 5,
            "avgTrustScore": 0.85,
            "humanOverrideRate": 0.15
        })
        assert stats.total_decisions == 100
        assert stats.bias_incidents == 5
    except ValidationError as e:
        print(f"  Model validation error: {e}")
        raise


def test_webhook_verification():
    """Test webhook signature verification"""
    print("✓ Testing webhook verification...")
    
    from athena.utils import verify_webhook_signature
    from athena.errors import ValidationError
    import hmac
    import hashlib
    import time
    
    secret = "test_secret"
    payload = '{"type": "test", "id": "123", "timestamp": "2025-12-25T00:00:00Z", "data": {}}'
    timestamp = int(time.time())
    
    # Generate valid signature
    signed_payload = f"{timestamp}.{payload}"
    signature = hmac.new(
        secret.encode(),
        signed_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    signature_header = f"t={timestamp},v1={signature}"
    
    # Should succeed with valid signature
    result = verify_webhook_signature(payload, signature_header, secret, tolerance=300)
    assert result is True
    
    # Should fail with invalid signature
    try:
        verify_webhook_signature(payload, f"t={timestamp},v1=invalid", secret)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass


def test_error_hierarchy():
    """Test error class hierarchy"""
    print("✓ Testing error hierarchy...")
    
    from athena.errors import (
        AthenaError,
        AuthenticationError,
        RateLimitError,
        ValidationError,
        NotFoundError
    )
    
    # All errors should inherit from AthenaError
    assert issubclass(AuthenticationError, AthenaError)
    assert issubclass(RateLimitError, AthenaError)
    assert issubclass(ValidationError, AthenaError)
    assert issubclass(NotFoundError, AthenaError)
    
    # Test error attributes
    error = RateLimitError(retry_after=60)
    assert error.status_code == 429
    assert error.retry_after == 60


def main():
    """Run all smoke tests"""
    print("\n═══════════════════════════════════════════════════════════")
    print("  🧪 ATHENA Python SDK - Smoke Test")
    print("═══════════════════════════════════════════════════════════\n")
    
    tests = [
        test_imports,
        test_client_initialization,
        test_async_client_initialization,
        test_models,
        test_webhook_verification,
        test_error_hierarchy
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n═══════════════════════════════════════════════════════════")
    print(f"  Results: {passed} passed, {failed} failed")
    print("═══════════════════════════════════════════════════════════\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

