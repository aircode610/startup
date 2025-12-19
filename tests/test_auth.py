import pytest

from app.auth import extract_bearer_token, validate_token


# =============================================================================
# extract_bearer_token tests
# =============================================================================

def test_extract_bearer_token_valid_format():
    """Happy path: properly formatted Bearer token"""
    result = extract_bearer_token("Bearer user_12345")
    assert result == "user_12345"


def test_extract_bearer_token_valid_with_extra_whitespace():
    """Token with leading/trailing whitespace should be stripped"""
    result = extract_bearer_token("Bearer   user_abc   ")
    assert result == "user_abc"


def test_extract_bearer_token_case_insensitive_scheme():
    """Bearer scheme should be case-insensitive"""
    assert extract_bearer_token("bearer user_123") == "user_123"
    assert extract_bearer_token("BEARER user_123") == "user_123"
    assert extract_bearer_token("BeArEr user_123") == "user_123"


def test_extract_bearer_token_none_header():
    """None header should return None"""
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


def test_extract_bearer_token_missing_token_part():
    """Header with only 'Bearer' (no token) should return None"""
    result = extract_bearer_token("Bearer")
    assert result is None


def test_extract_bearer_token_missing_scheme():
    """Token without scheme should return None"""
    result = extract_bearer_token("user_12345")
    assert result is None


def test_extract_bearer_token_wrong_scheme():
    """Non-Bearer scheme should return None"""
    assert extract_bearer_token("Basic user_123") is None
    assert extract_bearer_token("Token user_123") is None
    assert extract_bearer_token("OAuth user_123") is None


def test_extract_bearer_token_too_many_parts():
    """Header with more than 2 parts should return None"""
    result = extract_bearer_token("Bearer user_123 extra")
    assert result is None


def test_extract_bearer_token_empty_token_after_strip():
    """Token that becomes empty after strip should return None"""
    result = extract_bearer_token("Bearer    ")
    assert result is None


def test_extract_bearer_token_special_characters():
    """Tokens with special characters should be extracted correctly"""
    assert extract_bearer_token("Bearer user_123-abc.xyz") == "user_123-abc.xyz"
    assert extract_bearer_token("Bearer user_!@#$%") == "user_!@#$%"


def test_extract_bearer_token_long_token():
    """Very long tokens should be handled correctly"""
    long_token = "user_" + "a" * 1000
    result = extract_bearer_token(f"Bearer {long_token}")
    assert result == long_token


def test_extract_bearer_token_numeric_token():
    """Numeric-only tokens should be extracted"""
    result = extract_bearer_token("Bearer 123456")
    assert result == "123456"


# =============================================================================
# validate_token tests
# =============================================================================

def test_validate_token_valid_user_prefix():
    """Happy path: token starting with 'user_' should be valid"""
    assert validate_token("user_123") is True
    assert validate_token("user_abc") is True
    assert validate_token("user_") is True


def test_validate_token_valid_user_prefix_long():
    """Long tokens with user_ prefix should be valid"""
    assert validate_token("user_" + "x" * 1000) is True


def test_validate_token_invalid_prefix():
    """Tokens not starting with 'user_' should be invalid"""
    assert validate_token("admin_123") is False
    assert validate_token("token_123") is False
    assert validate_token("123_user") is False
    assert validate_token("USER_123") is False  # case-sensitive


def test_validate_token_empty_string():
    """Empty string should be invalid"""
    assert validate_token("") is False


def test_validate_token_none():
    """
    CRITICAL BUG TEST: None token causes AttributeError
    
    The current implementation removed the null check, so this will raise
    AttributeError instead of returning False. This test documents the bug.
    """
    with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'startswith'"):
        validate_token(None)


def test_validate_token_partial_match():
    """Tokens containing but not starting with 'user_' should be invalid"""
    assert validate_token("prefix_user_123") is False
    assert validate_token(" user_123") is False  # leading space


def test_validate_token_case_sensitive():
    """Validation should be case-sensitive"""
    assert validate_token("user_123") is True
    assert validate_token("User_123") is False
    assert validate_token("USER_123") is False


def test_validate_token_whitespace():
    """Whitespace-only strings should be invalid"""
    assert validate_token("   ") is False
    assert validate_token("\t") is False
    assert validate_token("\n") is False


def test_validate_token_special_characters_after_prefix():
    """Special characters after valid prefix should still be valid"""
    assert validate_token("user_!@#$%^&*()") is True
    assert validate_token("user_123-abc-xyz") is True
    assert validate_token("user_\n\t") is True


# =============================================================================
# Integration tests: extract_bearer_token -> validate_token pipeline
# =============================================================================

def test_integration_valid_bearer_to_valid_token():
    """Full flow: valid Bearer header -> valid token"""
    token = extract_bearer_token("Bearer user_12345")
    assert validate_token(token) is True


def test_integration_valid_bearer_to_invalid_token():
    """Full flow: valid Bearer header -> invalid token (wrong prefix)"""
    token = extract_bearer_token("Bearer admin_12345")
    assert validate_token(token) is False


def test_integration_invalid_bearer_returns_none():
    """Full flow: invalid Bearer header -> None token -> AttributeError"""
    token = extract_bearer_token("InvalidScheme token123")
    assert token is None
    # This will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_none_header():
    """Full flow: None header -> None token -> AttributeError"""
    token = extract_bearer_token(None)
    assert token is None
    # This will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_empty_header():
    """Full flow: empty header -> None token -> AttributeError"""
    token = extract_bearer_token("")
    assert token is None
    # This will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_malformed_bearer():
    """Full flow: malformed Bearer (too many parts) -> None token -> AttributeError"""
    token = extract_bearer_token("Bearer user_123 extra")
    assert token is None
    # This will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_case_insensitive_bearer_valid_token():
    """Full flow: lowercase 'bearer' -> valid user_ token"""
    token = extract_bearer_token("bearer user_xyz")
    assert token == "user_xyz"
    assert validate_token(token) is True


# =============================================================================
# Edge cases and defensive programming tests
# =============================================================================

def test_extract_bearer_token_unicode_characters():
    """Unicode characters in token should be handled"""
    result = extract_bearer_token("Bearer user_こんにちは")
    assert result == "user_こんにちは"


def test_validate_token_unicode_prefix():
    """Unicode characters after valid prefix should be valid"""
    assert validate_token("user_🚀") is True
    assert validate_token("user_测试") is True


def test_extract_bearer_token_tabs_and_newlines():
    """Headers with tabs/newlines should be rejected"""
    assert extract_bearer_token("Bearer\tuser_123") is None
    assert extract_bearer_token("Bearer\nuser_123") is None


def test_validate_token_only_prefix():
    """Token that is exactly 'user_' should be valid (startswith is True)"""
    assert validate_token("user_") is True


def test_extract_bearer_token_double_spaces():
    """Multiple spaces between Bearer and token should fail (splits into >2 parts)"""
    # "Bearer  token" splits into ["Bearer", "", "token"] = 3 parts
    result = extract_bearer_token("Bearer  user_123")
    assert result is None


def test_validate_token_numeric_after_prefix():
    """Numeric characters after prefix should be valid"""
    assert validate_token("user_000") is True
    assert validate_token("user_999999999") is True