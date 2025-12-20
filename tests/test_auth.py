import pytest

from app.auth import extract_bearer_token, validate_token


# ============================================================================
# extract_bearer_token() tests
# ============================================================================

def test_extract_bearer_token_valid_token():
    """Happy path: correctly formatted Bearer token"""
    result = extract_bearer_token("Bearer user_12345")
    assert result == "user_12345"


def test_extract_bearer_token_valid_with_extra_whitespace():
    """Bearer token with extra spaces around the token value"""
    result = extract_bearer_token("Bearer   user_abc   ")
    assert result == "user_abc"


def test_extract_bearer_token_case_insensitive_bearer():
    """Bearer scheme is case-insensitive"""
    assert extract_bearer_token("bearer user_test") == "user_test"
    assert extract_bearer_token("BEARER user_test") == "user_test"
    assert extract_bearer_token("BeArEr user_test") == "user_test"


def test_extract_bearer_token_none_header():
    """None header should return None"""
    result = extract_bearer_token(None)
    assert result is None


def test_extract_bearer_token_empty_string():
    """Empty string header should return None"""
    result = extract_bearer_token("")
    assert result is None


def test_extract_bearer_token_whitespace_only():
    """Whitespace-only header should return None"""
    result = extract_bearer_token("   ")
    assert result is None


def test_extract_bearer_token_missing_token():
    """Bearer without token should return None"""
    result = extract_bearer_token("Bearer")
    assert result is None


def test_extract_bearer_token_missing_token_with_space():
    """Bearer with trailing space but no token should return None"""
    result = extract_bearer_token("Bearer ")
    assert result is None


def test_extract_bearer_token_empty_token_after_bearer():
    """Bearer with only whitespace as token should return None"""
    result = extract_bearer_token("Bearer    ")
    assert result is None


def test_extract_bearer_token_wrong_scheme():
    """Non-Bearer scheme should return None"""
    assert extract_bearer_token("Basic user_12345") is None
    assert extract_bearer_token("Token user_12345") is None
    assert extract_bearer_token("OAuth user_12345") is None


def test_extract_bearer_token_too_many_parts():
    """More than 2 parts should return None"""
    result = extract_bearer_token("Bearer user_123 extra_part")
    assert result is None


def test_extract_bearer_token_no_space_separator():
    """Bearer concatenated with token (no space) should return None"""
    result = extract_bearer_token("Beareruser_12345")
    assert result is None


def test_extract_bearer_token_only_token_no_scheme():
    """Token without Bearer scheme should return None"""
    result = extract_bearer_token("user_12345")
    assert result is None


def test_extract_bearer_token_special_characters_in_token():
    """Token with special characters should be extracted correctly"""
    result = extract_bearer_token("Bearer user_123-abc.xyz")
    assert result == "user_123-abc.xyz"


def test_extract_bearer_token_numeric_token():
    """Numeric token should be extracted correctly"""
    result = extract_bearer_token("Bearer 1234567890")
    assert result == "1234567890"


def test_extract_bearer_token_jwt_like_token():
    """JWT-like token (with dots) should be extracted correctly"""
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    result = extract_bearer_token(f"Bearer {jwt_token}")
    assert result == jwt_token


def test_extract_bearer_token_unicode_characters():
    """Token with unicode characters should be handled"""
    result = extract_bearer_token("Bearer user_🔑_token")
    assert result == "user_🔑_token"


# ============================================================================
# validate_token() tests
# ============================================================================

def test_validate_token_valid_user_prefix():
    """Happy path: token starts with 'user_'"""
    assert validate_token("user_12345") is True


def test_validate_token_valid_minimal():
    """Minimal valid token: just 'user_'"""
    assert validate_token("user_") is True


def test_validate_token_valid_long_token():
    """Long valid token with user_ prefix"""
    long_token = "user_" + "a" * 1000
    assert validate_token(long_token) is True


def test_validate_token_valid_with_special_chars():
    """Valid token with special characters after user_"""
    assert validate_token("user_123-abc-xyz") is True
    assert validate_token("user_abc.def.ghi") is True
    assert validate_token("user_test@example") is True


def test_validate_token_invalid_empty_string():
    """Empty string should be invalid"""
    assert validate_token("") is False


def test_validate_token_invalid_wrong_prefix():
    """Token with wrong prefix should be invalid"""
    assert validate_token("admin_12345") is False
    assert validate_token("token_12345") is False
    assert validate_token("session_12345") is False


def test_validate_token_invalid_case_sensitive():
    """Prefix is case-sensitive: 'User_' or 'USER_' should be invalid"""
    assert validate_token("User_12345") is False
    assert validate_token("USER_12345") is False
    assert validate_token("UsEr_12345") is False


def test_validate_token_invalid_partial_match():
    """Tokens containing but not starting with 'user_' should be invalid"""
    assert validate_token("myuser_12345") is False
    assert validate_token("_user_12345") is False


def test_validate_token_invalid_whitespace_before_prefix():
    """Whitespace before 'user_' should make it invalid"""
    assert validate_token(" user_12345") is False
    assert validate_token("\tuser_12345") is False


def test_validate_token_invalid_no_underscore():
    """'user' without underscore should be invalid"""
    assert validate_token("user12345") is False
    assert validate_token("user") is False


def test_validate_token_none_raises_attribute_error():
    """
    CRITICAL BUG TEST: validate_token(None) should handle None gracefully,
    but after the recent change (removing the None check), it will raise
    AttributeError when trying to call .startswith() on None.
    
    This test documents the current broken behavior. The function should
    return False for None tokens instead of raising an exception.
    """
    with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'startswith'"):
        validate_token(None)


def test_validate_token_numeric_only():
    """Pure numeric token (no user_ prefix) should be invalid"""
    assert validate_token("12345") is False


def test_validate_token_special_chars_only():
    """Special characters without user_ prefix should be invalid"""
    assert validate_token("!@#$%^&*()") is False


def test_validate_token_underscore_only():
    """Just underscore should be invalid"""
    assert validate_token("_") is False


def test_validate_token_user_prefix_variations():
    """Test various near-misses of the user_ prefix"""
    assert validate_token("user-12345") is False  # dash instead of underscore
    assert validate_token("user.12345") is False  # dot instead of underscore
    assert validate_token("user 12345") is False  # space instead of underscore


# ============================================================================
# Integration tests: extract_bearer_token + validate_token
# ============================================================================

def test_integration_valid_bearer_token_flow():
    """End-to-end: valid Bearer token extraction and validation"""
    header = "Bearer user_abc123"
    token = extract_bearer_token(header)
    assert token == "user_abc123"
    assert validate_token(token) is True


def test_integration_invalid_token_in_valid_bearer():
    """End-to-end: valid Bearer format but invalid token"""
    header = "Bearer admin_12345"
    token = extract_bearer_token(header)
    assert token == "admin_12345"
    assert validate_token(token) is False


def test_integration_malformed_header():
    """End-to-end: malformed header results in None, which raises error in validate"""
    header = "InvalidHeader"
    token = extract_bearer_token(header)
    assert token is None
    
    # This will raise AttributeError due to the bug in validate_token
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_none_header():
    """End-to-end: None header results in None token, which raises error in validate"""
    token = extract_bearer_token(None)
    assert token is None
    
    # This will raise AttributeError due to the bug in validate_token
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_empty_header():
    """End-to-end: empty header results in None token, which raises error in validate"""
    token = extract_bearer_token("")
    assert token is None
    
    # This will raise AttributeError due to the bug in validate_token
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_case_insensitive_bearer_with_valid_token():
    """End-to-end: case-insensitive Bearer with valid token"""
    header = "bearer user_test123"
    token = extract_bearer_token(header)
    assert validate_token(token) is True


def test_integration_whitespace_handling():
    """End-to-end: Bearer token with extra whitespace"""
    header = "Bearer   user_trimmed   "
    token = extract_bearer_token(header)
    assert token == "user_trimmed"
    assert validate_token(token) is True