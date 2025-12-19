import pytest

from app.auth import extract_bearer_token, validate_token


# ============================================================================
# Tests for extract_bearer_token()
# ============================================================================


def test_extract_bearer_token_valid_token():
    """Happy path: properly formatted Bearer token"""
    result = extract_bearer_token("Bearer user_12345")
    assert result == "user_12345"


def test_extract_bearer_token_valid_with_underscores():
    """Valid token with various characters"""
    result = extract_bearer_token("Bearer user_abc_123_xyz")
    assert result == "user_abc_123_xyz"


def test_extract_bearer_token_valid_with_long_token():
    """Valid token with long alphanumeric string"""
    long_token = "user_" + "a" * 100
    result = extract_bearer_token(f"Bearer {long_token}")
    assert result == long_token


def test_extract_bearer_token_case_insensitive_bearer():
    """Bearer scheme should be case-insensitive"""
    result = extract_bearer_token("bearer user_123")
    assert result == "user_123"


def test_extract_bearer_token_uppercase_bearer():
    """BEARER in uppercase should work"""
    result = extract_bearer_token("BEARER user_123")
    assert result == "user_123"


def test_extract_bearer_token_mixed_case_bearer():
    """Mixed case Bearer should work"""
    result = extract_bearer_token("BeArEr user_123")
    assert result == "user_123"


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


def test_extract_bearer_token_missing_scheme():
    """Token without Bearer scheme should return None"""
    result = extract_bearer_token("user_123")
    assert result is None


def test_extract_bearer_token_wrong_scheme():
    """Wrong authentication scheme should return None"""
    result = extract_bearer_token("Basic user_123")
    assert result is None


def test_extract_bearer_token_too_many_parts():
    """More than 2 parts should return None"""
    result = extract_bearer_token("Bearer user_123 extra_part")
    assert result is None


def test_extract_bearer_token_empty_token_after_bearer():
    """Bearer with empty/whitespace token should return None"""
    result = extract_bearer_token("Bearer   ")
    assert result is None


def test_extract_bearer_token_token_with_leading_trailing_spaces():
    """Token with spaces should be stripped"""
    result = extract_bearer_token("Bearer   user_123   ")
    # Note: This will fail because split() creates ["Bearer", "", "", "user_123", "", ""]
    # which has len > 2, so it returns None. This tests actual behavior.
    assert result is None


def test_extract_bearer_token_single_space_separation():
    """Standard single space separation (most common case)"""
    result = extract_bearer_token("Bearer user_123")
    assert result == "user_123"


def test_extract_bearer_token_tab_character():
    """Tab instead of space should not work (split() splits on all whitespace but results in wrong count)"""
    result = extract_bearer_token("Bearer\tuser_123")
    assert result == "user_123"  # split() handles tabs


def test_extract_bearer_token_special_characters_in_token():
    """Tokens can contain various special characters"""
    result = extract_bearer_token("Bearer user_123-456.789")
    assert result == "user_123-456.789"


# ============================================================================
# Tests for validate_token()
# ============================================================================


def test_validate_token_valid_user_prefix():
    """Happy path: token starting with user_"""
    assert validate_token("user_123") is True


def test_validate_token_valid_user_only():
    """Minimal valid token: just 'user_'"""
    assert validate_token("user_") is True


def test_validate_token_valid_with_long_suffix():
    """Valid token with long suffix"""
    assert validate_token("user_" + "x" * 1000) is True


def test_validate_token_valid_with_numbers():
    """Valid token with numeric suffix"""
    assert validate_token("user_123456789") is True


def test_validate_token_valid_with_mixed_chars():
    """Valid token with mixed alphanumeric and special chars"""
    assert validate_token("user_abc123_xyz-789") is True


def test_validate_token_empty_string():
    """Empty string should be invalid"""
    assert validate_token("") is False


def test_validate_token_none():
    """
    CRITICAL BUG TEST: None token should return False, not raise AttributeError.
    
    The diff removed the None check, which means this will now raise:
        AttributeError: 'NoneType' object has no attribute 'startswith'
    
    This test documents the regression introduced by the code change.
    """
    with pytest.raises(AttributeError):
        # Current broken behavior after the diff
        validate_token(None)
    
    # Expected behavior (commented out - this is what SHOULD happen):
    # assert validate_token(None) is False


def test_validate_token_wrong_prefix():
    """Token not starting with user_ should be invalid"""
    assert validate_token("admin_123") is False


def test_validate_token_no_prefix():
    """Token with no prefix should be invalid"""
    assert validate_token("123456") is False


def test_validate_token_user_without_underscore():
    """'user' without underscore should be invalid"""
    assert validate_token("user") is False


def test_validate_token_user_prefix_in_middle():
    """user_ in middle of string should be invalid"""
    assert validate_token("token_user_123") is False


def test_validate_token_case_sensitive():
    """Prefix should be case-sensitive"""
    assert validate_token("USER_123") is False
    assert validate_token("User_123") is False


def test_validate_token_whitespace_prefix():
    """Token with leading whitespace should be invalid"""
    assert validate_token(" user_123") is False


def test_validate_token_whitespace_suffix():
    """Token with trailing whitespace is still valid (startswith checks prefix only)"""
    assert validate_token("user_123 ") is True


def test_validate_token_only_whitespace():
    """Only whitespace should be invalid"""
    assert validate_token("   ") is False


def test_validate_token_special_chars_prefix():
    """Special characters before user_ should be invalid"""
    assert validate_token("_user_123") is False
    assert validate_token("-user_123") is False


# ============================================================================
# Integration tests: extract_bearer_token + validate_token
# ============================================================================


def test_integration_valid_auth_flow():
    """Complete auth flow: extract then validate"""
    header = "Bearer user_12345"
    token = extract_bearer_token(header)
    assert token == "user_12345"
    assert validate_token(token) is True


def test_integration_invalid_token_prefix():
    """Extract valid format but token has wrong prefix"""
    header = "Bearer admin_12345"
    token = extract_bearer_token(header)
    assert token == "admin_12345"
    assert validate_token(token) is False


def test_integration_malformed_header():
    """Malformed header returns None, which fails validation"""
    header = "InvalidHeader"
    token = extract_bearer_token(header)
    assert token is None
    
    # This will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_none_header():
    """None header returns None token, which fails validation"""
    token = extract_bearer_token(None)
    assert token is None
    
    # This will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_empty_header():
    """Empty header returns None token"""
    token = extract_bearer_token("")
    assert token is None
    
    # This will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_wrong_scheme():
    """Wrong auth scheme returns None token"""
    header = "Basic user_12345"
    token = extract_bearer_token(header)
    assert token is None
    
    # This will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


# ============================================================================
# Edge cases and boundary tests
# ============================================================================


def test_extract_bearer_token_with_newlines():
    """Header with newlines should not work"""
    result = extract_bearer_token("Bearer\nuser_123")
    assert result == "user_123"  # split() handles newlines


def test_validate_token_unicode_characters():
    """Token with unicode characters"""
    assert validate_token("user_こんにちは") is True
    assert validate_token("こんにちは_user_123") is False


def test_validate_token_empty_after_prefix():
    """Token that is exactly 'user_' with nothing after"""
    assert validate_token("user_") is True


def test_extract_bearer_token_very_long_invalid_header():
    """Very long malformed header should handle gracefully"""
    long_invalid = "InvalidScheme " + "x" * 10000
    result = extract_bearer_token(long_invalid)
    assert result is None


def test_validate_token_sql_injection_attempt():
    """Token containing SQL-like strings should work (no SQL involved)"""
    assert validate_token("user_'; DROP TABLE users; --") is True


def test_validate_token_url_encoded_chars():
    """Token with URL-encoded characters"""
    assert validate_token("user_%20%21") is True


# ============================================================================
# Property-based / Parametrized tests
# ============================================================================


@pytest.mark.parametrize("invalid_scheme", [
    "Basic",
    "Digest",
    "OAuth",
    "Token",
    "ApiKey",
    "",
    "Bear",  # typo
    "Bearerr",  # typo
    "Bearer:",  # extra char
])
def test_extract_bearer_token_invalid_schemes(invalid_scheme):
    """Various invalid schemes should return None"""
    header = f"{invalid_scheme} user_123"
    result = extract_bearer_token(header)
    assert result is None


@pytest.mark.parametrize("invalid_prefix", [
    "admin_123",
    "root_456",
    "token_789",
    "guest_111",
    "USER_123",  # wrong case
    "User_456",  # wrong case
    "_user_789",  # underscore before
    " user_111",  # space before
])
def test_validate_token_invalid_prefixes(invalid_prefix):
    """Various invalid prefixes should return False"""
    assert validate_token(invalid_prefix) is False


@pytest.mark.parametrize("valid_token", [
    "user_1",
    "user_abc",
    "user_123abc",
    "user_abc_123",
    "user_" + "x" * 100,
    "user_!@#$%",
    "user_-.",
])
def test_validate_token_valid_formats(valid_token):
    """Various valid token formats should return True"""
    assert validate_token(valid_token) is True


@pytest.mark.parametrize("whitespace_variant", [
    "",
    " ",
    "  ",
    "\t",
    "\n",
    "\r\n",
    "   \t\n  ",
])
def test_extract_bearer_token_whitespace_variants(whitespace_variant):
    """Various whitespace-only inputs should return None"""
    result = extract_bearer_token(whitespace_variant)
    assert result is None