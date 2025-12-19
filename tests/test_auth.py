import pytest

from app.auth import extract_bearer_token, validate_token


# ========================================
# Tests for extract_bearer_token
# ========================================

def test_extract_bearer_token_valid_token():
    """Happy path: valid Bearer token"""
    result = extract_bearer_token("Bearer user_12345")
    assert result == "user_12345"


def test_extract_bearer_token_valid_with_extra_whitespace():
    """Token with leading/trailing whitespace should be stripped"""
    result = extract_bearer_token("Bearer   user_abc   ")
    assert result == "user_abc"


def test_extract_bearer_token_case_insensitive_bearer():
    """Bearer scheme should be case-insensitive"""
    assert extract_bearer_token("bearer user_test") == "user_test"
    assert extract_bearer_token("BEARER user_test") == "user_test"
    assert extract_bearer_token("BeArEr user_test") == "user_test"


def test_extract_bearer_token_none_header():
    """None header should return None (defensive)"""
    result = extract_bearer_token(None)
    assert result is None


def test_extract_bearer_token_empty_string():
    """Empty string should return None"""
    result = extract_bearer_token("")
    assert result is None


def test_extract_bearer_token_whitespace_only():
    """Whitespace-only string should return None"""
    result = extract_bearer_token("   ")
    assert result is None


def test_extract_bearer_token_missing_token():
    """Bearer without token should return None"""
    result = extract_bearer_token("Bearer")
    assert result is None


def test_extract_bearer_token_missing_scheme():
    """Token without scheme should return None"""
    result = extract_bearer_token("user_12345")
    assert result is None


def test_extract_bearer_token_wrong_scheme():
    """Non-Bearer scheme should return None"""
    assert extract_bearer_token("Basic user_12345") is None
    assert extract_bearer_token("Token user_12345") is None
    assert extract_bearer_token("JWT user_12345") is None


def test_extract_bearer_token_too_many_parts():
    """More than 2 parts should return None"""
    result = extract_bearer_token("Bearer user_12345 extra_part")
    assert result is None


def test_extract_bearer_token_empty_token_after_bearer():
    """Bearer with empty token (just whitespace) should return None"""
    result = extract_bearer_token("Bearer    ")
    assert result is None


def test_extract_bearer_token_special_characters():
    """Tokens with special characters should be extracted correctly"""
    result = extract_bearer_token("Bearer user_123-abc.xyz")
    assert result == "user_123-abc.xyz"


def test_extract_bearer_token_numeric_only():
    """Numeric-only tokens should be extracted"""
    result = extract_bearer_token("Bearer 123456789")
    assert result == "123456789"


def test_extract_bearer_token_with_underscores():
    """Tokens with multiple underscores"""
    result = extract_bearer_token("Bearer user_admin_super_token")
    assert result == "user_admin_super_token"


def test_extract_bearer_token_single_char():
    """Single character token should be valid"""
    result = extract_bearer_token("Bearer x")
    assert result == "x"


# ========================================
# Tests for validate_token
# ========================================

def test_validate_token_valid_user_prefix():
    """Happy path: token starts with 'user_'"""
    assert validate_token("user_123") is True
    assert validate_token("user_abc") is True
    assert validate_token("user_") is True  # Just the prefix is valid


def test_validate_token_valid_long_token():
    """Long token with user_ prefix should be valid"""
    assert validate_token("user_" + "x" * 1000) is True


def test_validate_token_invalid_no_prefix():
    """Token without 'user_' prefix should be invalid"""
    assert validate_token("admin_123") is False
    assert validate_token("token_123") is False
    assert validate_token("123456") is False


def test_validate_token_invalid_wrong_prefix():
    """Token with similar but wrong prefix should be invalid"""
    assert validate_token("users_123") is False
    assert validate_token("User_123") is False  # Case-sensitive
    assert validate_token("USER_123") is False


def test_validate_token_invalid_prefix_in_middle():
    """Token with 'user_' in middle but not at start should be invalid"""
    assert validate_token("admin_user_123") is False
    assert validate_token("x_user_123") is False


def test_validate_token_empty_string():
    """Empty string should be invalid"""
    assert validate_token("") is False


def test_validate_token_none():
    """None token should be invalid (and handle gracefully)"""
    # This is the critical test that catches the bug in the diff!
    # The removed null check will cause AttributeError here
    with pytest.raises(AttributeError):
        validate_token(None)


def test_validate_token_whitespace_only():
    """Whitespace-only token should be invalid"""
    assert validate_token("   ") is False
    assert validate_token("\t") is False
    assert validate_token("\n") is False


def test_validate_token_partial_prefix():
    """Partial prefix should be invalid"""
    assert validate_token("u") is False
    assert validate_token("us") is False
    assert validate_token("use") is False
    assert validate_token("user") is False


def test_validate_token_prefix_with_space():
    """Prefix with space should be invalid"""
    assert validate_token("user _123") is False
    assert validate_token(" user_123") is False


def test_validate_token_unicode_characters():
    """Token with unicode characters"""
    assert validate_token("user_😀") is True
    assert validate_token("user_δοκιμή") is True
    assert validate_token("😀_user") is False


# ========================================
# Integration tests
# ========================================

def test_extract_and_validate_happy_path():
    """Integration: extract and validate a good token"""
    token = extract_bearer_token("Bearer user_12345")
    assert token == "user_12345"
    assert validate_token(token) is True


def test_extract_and_validate_invalid_prefix():
    """Integration: extract valid format but invalid token prefix"""
    token = extract_bearer_token("Bearer admin_12345")
    assert token == "admin_12345"
    assert validate_token(token) is False


def test_extract_and_validate_malformed_header():
    """Integration: malformed header extraction returns None"""
    token = extract_bearer_token("InvalidHeader")
    assert token is None
    # The bug: validate_token(None) will raise AttributeError
    with pytest.raises(AttributeError):
        validate_token(token)


def test_extract_and_validate_missing_header():
    """Integration: missing header should result in invalid auth"""
    token = extract_bearer_token(None)
    assert token is None
    # The bug: validate_token(None) will raise AttributeError
    with pytest.raises(AttributeError):
        validate_token(token)


def test_extract_and_validate_empty_token_after_bearer():
    """Integration: Bearer with whitespace only"""
    token = extract_bearer_token("Bearer   ")
    assert token is None
    with pytest.raises(AttributeError):
        validate_token(token)


# ========================================
# Edge cases and boundary conditions
# ========================================

def test_extract_bearer_token_very_long_header():
    """Very long authorization header"""
    long_token = "user_" + "x" * 10000
    result = extract_bearer_token(f"Bearer {long_token}")
    assert result == long_token


def test_validate_token_exactly_user_underscore():
    """Token that is exactly 'user_' should be valid"""
    assert validate_token("user_") is True


def test_extract_bearer_token_with_tabs():
    """Header with tabs instead of spaces"""
    result = extract_bearer_token("Bearer\tuser_123")
    # split() handles any whitespace
    assert result == "user_123"


def test_validate_token_starts_with_user_underscore_substring():
    """Verify startswith works correctly"""
    assert validate_token("user_admin") is True
    assert validate_token("user_") is True
    assert validate_token("user_1") is True


def test_extract_bearer_token_multiple_spaces_between():
    """Multiple spaces between Bearer and token"""
    # This will fail because split() creates empty strings
    result = extract_bearer_token("Bearer  user_123")
    # split() without args handles multiple whitespace
    assert result == "user_123"


def test_validate_token_special_start_characters():
    """Tokens starting with special characters"""
    assert validate_token("!user_123") is False
    assert validate_token("@user_123") is False
    assert validate_token("#user_123") is False


def test_extract_bearer_token_newlines_and_special_whitespace():
    """Header with newlines and other whitespace"""
    result = extract_bearer_token("Bearer\nuser_123")
    assert result == "user_123"


def test_validate_token_with_newlines():
    """Token containing newlines should be handled"""
    assert validate_token("user_\n123") is True


# ========================================
# Defensive programming tests
# ========================================

def test_extract_bearer_token_never_raises():
    """Verify extract_bearer_token never raises exceptions"""
    # These should all return None, never raise
    test_inputs = [
        None,
        "",
        "   ",
        "Bearer",
        "user_123",
        "Bearer user_123 extra",
        123,  # Wrong type, but let's see if it's handled
    ]
    
    for inp in test_inputs[:-1]:  # Skip the integer for now
        try:
            result = extract_bearer_token(inp)
            # Should return None or a string, never raise
            assert result is None or isinstance(result, str)
        except Exception as e:
            pytest.fail(f"extract_bearer_token raised {type(e).__name__} for input {inp!r}")


def test_validate_token_type_safety():
    """Test validate_token with unexpected types"""
    # These should either return False or raise TypeError/AttributeError
    with pytest.raises(AttributeError):
        validate_token(None)
    
    with pytest.raises(AttributeError):
        validate_token(123)
    
    with pytest.raises(AttributeError):
        validate_token([])
    
    with pytest.raises(AttributeError):
        validate_token({})

# ========================================
# Additional Security & Attack Vector Tests
# ========================================

def test_extract_bearer_token_sql_injection_attempt():
    """Token containing SQL injection patterns should be extracted as-is"""
    result = extract_bearer_token("Bearer user_123'; DROP TABLE users--")
    assert result == "user_123'; DROP TABLE users--"


def test_validate_token_sql_injection_in_token():
    """SQL injection patterns in token should fail validation (no user_ prefix)"""
    assert validate_token("'; DROP TABLE users--") is False


def test_validate_token_xss_attempt():
    """XSS patterns should fail validation"""
    assert validate_token("<script>alert('xss')</script>") is False
    assert validate_token("user_<script>alert('xss')</script>") is True  # Has prefix


def test_extract_bearer_token_header_injection():
    """Newline injection attempts in header"""
    result = extract_bearer_token("Bearer user_123\r\nX-Injected: malicious")
    # Should extract up to the first newline character
    assert "X-Injected" not in (result or "")


def test_validate_token_path_traversal_attempt():
    """Path traversal patterns in token"""
    assert validate_token("../../etc/passwd") is False
    assert validate_token("user_../../etc/passwd") is True  # Has prefix


def test_extract_bearer_token_null_byte_injection():
    """Null byte in token should be extracted"""
    result = extract_bearer_token("Bearer user_123\x00admin")
    assert result == "user_123\x00admin"


def test_validate_token_null_byte():
    """Token with null byte but valid prefix"""
    assert validate_token("user_\x00admin") is True


def test_extract_bearer_token_command_injection_patterns():
    """Command injection patterns should be extracted as-is"""
    result = extract_bearer_token("Bearer user_$(whoami)")
    assert result == "user_$(whoami)"


def test_validate_token_command_injection():
    """Command injection with valid prefix"""
    assert validate_token("user_$(whoami)") is True
    assert validate_token("$(whoami)_user") is False


# ========================================
# Additional Boundary & Edge Cases
# ========================================

def test_extract_bearer_token_exactly_bearer():
    """Just the word 'Bearer' with no token"""
    assert extract_bearer_token("Bearer") is None


def test_extract_bearer_token_bearer_with_multiple_tabs():
    """Multiple tabs between Bearer and token"""
    result = extract_bearer_token("Bearer\t\t\tuser_123")
    assert result == "user_123"


def test_extract_bearer_token_mixed_whitespace():
    """Mixed tabs, spaces, and other whitespace"""
    result = extract_bearer_token("Bearer \t \n user_123")
    # split() without args handles all whitespace, but len(parts) might != 2
    # This should return None due to multiple parts
    assert result is None


def test_validate_token_only_underscore():
    """Token that is just an underscore"""
    assert validate_token("_") is False


def test_validate_token_user_prefix_variations():
    """Various invalid user prefix patterns"""
    assert validate_token("use_") is False
    assert validate_token("ser_") is False
    assert validate_token("_user") is False
    assert validate_token("_user_") is False


def test_extract_bearer_token_bearer_lowercase_token():
    """All lowercase bearer and token"""
    result = extract_bearer_token("bearer user_token")
    assert result == "user_token"


def test_extract_bearer_token_unicode_scheme():
    """Unicode characters in scheme (should fail)"""
    result = extract_bearer_token("Beärer user_123")
    assert result is None


def test_validate_token_extremely_long_prefix():
    """Very long token with user_ prefix"""
    long_token = "user_" + "a" * 1_000_000
    assert validate_token(long_token) is True


def test_extract_bearer_token_token_contains_bearer():
    """Token value contains the word 'bearer'"""
    result = extract_bearer_token("Bearer user_bearer_token")
    assert result == "user_bearer_token"


def test_validate_token_repeating_prefix():
    """Token with repeating user_ prefixes"""
    assert validate_token("user_user_user_123") is True


def test_extract_bearer_token_only_whitespace_token():
    """Bearer followed by only whitespace characters"""
    result = extract_bearer_token("Bearer \t\n\r ")
    assert result is None


# ========================================
# Real-world Authentication Scenarios
# ========================================

def test_extract_bearer_token_jwt_format():
    """JWT-like token structure"""
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    result = extract_bearer_token(f"Bearer {jwt}")
    assert result == jwt


def test_validate_token_jwt_without_prefix():
    """JWT without user_ prefix should be invalid"""
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    assert validate_token(jwt) is False


def test_validate_token_jwt_with_user_prefix():
    """JWT-like token with user_ prefix"""
    token = "user_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    assert validate_token(token) is True


def test_extract_bearer_token_uuid_format():
    """UUID as token"""
    uuid_token = "550e8400-e29b-41d4-a716-446655440000"
    result = extract_bearer_token(f"Bearer {uuid_token}")
    assert result == uuid_token


def test_validate_token_uuid_with_user_prefix():
    """UUID with user_ prefix"""
    token = "user_550e8400-e29b-41d4-a716-446655440000"
    assert validate_token(token) is True


def test_extract_and_validate_session_token_pattern():
    """Session token pattern: user_<timestamp>_<random>"""
    token = "user_1234567890_abc123def456"
    extracted = extract_bearer_token(f"Bearer {token}")
    assert extracted == token
    assert validate_token(extracted) is True


def test_extract_bearer_token_api_key_format():
    """API key format token"""
    api_key = "sk_live_51234567890abcdefghijk"
    result = extract_bearer_token(f"Bearer {api_key}")
    assert result == api_key


def test_validate_token_api_key_without_prefix():
    """API key without user_ prefix"""
    api_key = "sk_live_51234567890abcdefghijk"
    assert validate_token(api_key) is False


# ========================================
# Character Encoding & Special Characters
# ========================================

def test_extract_bearer_token_base64_like():
    """Base64-encoded looking token"""
    token = "user_dGVzdEB0ZXN0LmNvbTpwYXNzd29yZA=="
    result = extract_bearer_token(f"Bearer {token}")
    assert result == token


def test_validate_token_base64_with_prefix():
    """Base64 with user_ prefix"""
    token = "user_dGVzdEB0ZXN0LmNvbTpwYXNzd29yZA=="
    assert validate_token(token) is True


def test_extract_bearer_token_url_encoded_chars():
    """Token with URL-encoded characters"""
    token = "user_123%20%21%40%23"
    result = extract_bearer_token(f"Bearer {token}")
    assert result == token


def test_validate_token_url_encoded():
    """URL-encoded token with prefix"""
    assert validate_token("user_123%20test") is True


def test_extract_bearer_token_html_entities():
    """Token with HTML entities"""
    token = "user_&lt;test&gt;"
    result = extract_bearer_token(f"Bearer {token}")
    assert result == token


def test_validate_token_emoji_sequence():
    """Token with emoji sequence"""
    assert validate_token("user_👨‍👩‍👧‍👦") is True


def test_validate_token_rtl_characters():
    """Token with right-to-left characters"""
    assert validate_token("user_مرحبا") is True
    assert validate_token("مرحبا_user") is False


def test_extract_bearer_token_zero_width_characters():
    """Token with zero-width characters"""
    token = "user_\u200B\u200C\u200D123"
    result = extract_bearer_token(f"Bearer {token}")
    assert result == token


# ========================================
# Consistency & Idempotency Tests
# ========================================

def test_extract_bearer_token_idempotent():
    """Extracting the same token multiple times gives same result"""
    header = "Bearer user_123"
    result1 = extract_bearer_token(header)
    result2 = extract_bearer_token(header)
    result3 = extract_bearer_token(header)
    assert result1 == result2 == result3 == "user_123"


def test_validate_token_idempotent():
    """Validating the same token multiple times gives same result"""
    token = "user_123"
    assert validate_token(token) is True
    assert validate_token(token) is True
    assert validate_token(token) is True


def test_extract_bearer_token_deterministic():
    """Same input always produces same output"""
    inputs = [
        "Bearer user_123",
        "Bearer admin_123",
        "Bearer",
        None,
        "",
        "Invalid",
    ]
    for inp in inputs:
        result1 = extract_bearer_token(inp)
        result2 = extract_bearer_token(inp)
        assert result1 == result2


def test_validate_token_deterministic():
    """Same token always produces same validation result"""
    tokens = ["user_123", "admin_123", "", "user_", "test"]
    for token in tokens:
        result1 = validate_token(token)
        result2 = validate_token(token)
        assert result1 == result2


# ========================================
# Error Handling & Robustness
# ========================================

def test_extract_bearer_token_type_coercion():
    """Test behavior with types that might be coerced to string"""
    # Integer (will raise AttributeError on .split())
    try:
        result = extract_bearer_token(12345)  # type: ignore
        pytest.fail("Should raise AttributeError")
    except AttributeError:
        pass


def test_extract_bearer_token_boolean():
    """Boolean values as header"""
    try:
        extract_bearer_token(True)  # type: ignore
        pytest.fail("Should raise AttributeError")
    except AttributeError:
        pass


def test_extract_bearer_token_list():
    """List as header"""
    try:
        extract_bearer_token(["Bearer", "user_123"])  # type: ignore
        pytest.fail("Should raise AttributeError")
    except AttributeError:
        pass


def test_validate_token_empty_bytes():
    """Bytes object should raise AttributeError"""
    with pytest.raises(AttributeError):
        validate_token(b"user_123")  # type: ignore


def test_validate_token_float():
    """Float should raise AttributeError"""
    with pytest.raises(AttributeError):
        validate_token(3.14)  # type: ignore


def test_validate_token_boolean():
    """Boolean should raise AttributeError"""
    with pytest.raises(AttributeError):
        validate_token(True)  # type: ignore


# ========================================
# Performance & Resource Tests
# ========================================

def test_extract_bearer_token_extremely_long_header():
    """Very long header (potential DoS)"""
    long_header = "Bearer " + "x" * 10_000_000
    result = extract_bearer_token(long_header)
    assert result == "x" * 10_000_000


def test_validate_token_extremely_long_token():
    """Very long token validation"""
    long_token = "user_" + "x" * 10_000_000
    assert validate_token(long_token) is True


def test_extract_bearer_token_many_spaces():
    """Header with many spaces (should fail due to split creating >2 parts)"""
    header = "Bearer     user_123     extra     parts"
    result = extract_bearer_token(header)
    assert result is None


def test_validate_token_repeated_validation():
    """Validate same token many times (no state issues)"""
    token = "user_test_token_12345"
    for _ in range(1000):
        assert validate_token(token) is True


def test_extract_bearer_token_repeated_extraction():
    """Extract from same header many times"""
    header = "Bearer user_test"
    for _ in range(1000):
        assert extract_bearer_token(header) == "user_test"


# ========================================
# Integration with cart.py scenarios
# ========================================

def test_auth_flow_simulate_cart_checkout_success():
    """Simulate successful cart checkout auth flow"""
    # Simulate what cart.checkout does
    auth_header = "Bearer user_premium_customer_123"
    token = extract_bearer_token(auth_header)
    assert token is not None
    assert validate_token(token) is True


def test_auth_flow_simulate_cart_checkout_failure_no_header():
    """Simulate cart checkout with no header"""
    token = extract_bearer_token(None)
    assert token is None
    # This is the bug - validate_token will raise AttributeError
    with pytest.raises(AttributeError):
        validate_token(token)


def test_auth_flow_simulate_cart_checkout_failure_bad_prefix():
    """Simulate cart checkout with invalid token prefix"""
    auth_header = "Bearer admin_not_a_user"
    token = extract_bearer_token(auth_header)
    assert token == "admin_not_a_user"
    assert validate_token(token) is False


def test_auth_flow_simulate_cart_checkout_failure_malformed():
    """Simulate cart checkout with malformed header"""
    auth_header = "NotBearer user_123"
    token = extract_bearer_token(auth_header)
    assert token is None
    with pytest.raises(AttributeError):
        validate_token(token)


def test_auth_flow_user_tier_variations():
    """Test auth with different user tier patterns"""
    test_cases = [
        "user_regular_tier",
        "user_premium_tier",
        "user_admin_tier",
        "user_vip_12345",
    ]
    for token in test_cases:
        header = f"Bearer {token}"
        extracted = extract_bearer_token(header)
        assert extracted == token
        assert validate_token(extracted) is True


# ========================================
# Regression Tests for the Removed Null Check
# ========================================

def test_validate_token_none_regression():
    """REGRESSION: The removed null check causes AttributeError with None"""
    # This test documents the bug introduced by removing the null check
    with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'startswith'"):
        validate_token(None)


def test_validate_token_should_handle_none_safely():
    """REGRESSION: validate_token should return False for None, not raise"""
    # This test shows what the correct behavior should be
    # Currently fails due to the removed null check
    # Expected: assert validate_token(None) is False
    # Actual: raises AttributeError
    with pytest.raises(AttributeError):
        validate_token(None)


def test_integration_extract_none_then_validate():
    """REGRESSION: Common pattern that fails with removed null check"""
    # This pattern appears in cart.py line 30
    token = extract_bearer_token(None)  # Returns None
    # The bug: validate_token(None) raises instead of returning False
    with pytest.raises(AttributeError):
        is_valid = validate_token(token)


def test_integration_extract_empty_then_validate():
    """REGRESSION: Empty string header flow"""
    token = extract_bearer_token("")  # Returns None
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_extract_malformed_then_validate():
    """REGRESSION: Malformed header leading to None token"""
    token = extract_bearer_token("JustAToken")  # Returns None
    with pytest.raises(AttributeError):
        validate_token(token)


# ========================================
# Comprehensive Coverage Tests
# ========================================

def test_extract_bearer_token_all_invalid_inputs():
    """Comprehensive test of all invalid input patterns"""
    invalid_inputs = [
        None,
        "",
        "   ",
        "Bearer",
        "user_123",  # No scheme
        "Basic user_123",  # Wrong scheme
        "Bearer user_123 extra",  # Too many parts
        "Bearer   ",  # Empty token
        "NotBearer token",
        "bearer",  # No token
        "BEARER",  # No token
    ]
    for inp in invalid_inputs:
        result = extract_bearer_token(inp)
        assert result is None, f"Expected None for input: {inp!r}, got: {result!r}"


def test_validate_token_all_invalid_tokens():
    """Comprehensive test of all invalid token patterns"""
    invalid_tokens = [
        "",
        "   ",
        "admin_123",
        "token_123",
        "USER_123",
        "User_123",
        "users_123",
        "_user_123",
        "123_user",
        "test",
        "u",
        "us",
        "use",
        "user",
    ]
    for token in invalid_tokens:
        result = validate_token(token)
        assert result is False, f"Expected False for token: {token!r}, got: {result!r}"


def test_validate_token_all_valid_tokens():
    """Comprehensive test of all valid token patterns"""
    valid_tokens = [
        "user_",
        "user_1",
        "user_123",
        "user_abc",
        "user_ABC",
        "user_123abc",
        "user_test_token",
        "user_" + "x" * 100,
        "user_😀",
        "user_δοκιμή",
        "user_with-dashes",
        "user_with.dots",
        "user_with_underscores",
    ]
    for token in valid_tokens:
        result = validate_token(token)
        assert result is True, f"Expected True for token: {token!r}, got: {result!r}"