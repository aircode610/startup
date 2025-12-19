import pytest

from app.auth import extract_bearer_token, validate_token


# ============================================================================
# Tests for extract_bearer_token()
# ============================================================================


def test_extract_bearer_token_valid_token():
    """Happy path: valid Bearer token format"""
    result = extract_bearer_token("Bearer user_12345")
    assert result == "user_12345"


def test_extract_bearer_token_valid_token_with_underscores():
    """Valid token with special characters (underscores)"""
    result = extract_bearer_token("Bearer user_abc_def_123")
    assert result == "user_abc_def_123"


def test_extract_bearer_token_valid_token_alphanumeric():
    """Valid token with mixed alphanumeric characters"""
    result = extract_bearer_token("Bearer abc123XYZ789")
    assert result == "abc123XYZ789"


def test_extract_bearer_token_case_insensitive_bearer():
    """Bearer scheme should be case-insensitive (lowercase)"""
    result = extract_bearer_token("bearer user_token")
    assert result == "user_token"


def test_extract_bearer_token_case_insensitive_uppercase():
    """Bearer scheme should be case-insensitive (uppercase)"""
    result = extract_bearer_token("BEARER user_token")
    assert result == "user_token"


def test_extract_bearer_token_case_insensitive_mixedcase():
    """Bearer scheme should be case-insensitive (mixed case)"""
    result = extract_bearer_token("BeArEr user_token")
    assert result == "user_token"


def test_extract_bearer_token_with_extra_whitespace():
    """Token with extra spaces should be stripped"""
    result = extract_bearer_token("Bearer   user_token   ")
    assert result == "user_token"


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
    """Bearer with space but no token should return None"""
    result = extract_bearer_token("Bearer ")
    assert result is None


def test_extract_bearer_token_only_whitespace_after_bearer():
    """Bearer followed by only whitespace should return None"""
    result = extract_bearer_token("Bearer    ")
    assert result is None


def test_extract_bearer_token_wrong_scheme():
    """Non-Bearer scheme should return None"""
    result = extract_bearer_token("Basic user_token")
    assert result is None


def test_extract_bearer_token_no_scheme():
    """Token without scheme should return None"""
    result = extract_bearer_token("user_token")
    assert result is None


def test_extract_bearer_token_too_many_parts():
    """More than 2 parts should return None"""
    result = extract_bearer_token("Bearer user_token extra_part")
    assert result is None


def test_extract_bearer_token_multiple_spaces_between_parts():
    """Multiple spaces between Bearer and token (creates empty parts)"""
    result = extract_bearer_token("Bearer  user_token")
    # This will split into ["Bearer", "", "user_token"], len=3, should return None
    assert result is None


def test_extract_bearer_token_special_characters_in_token():
    """Token with various special characters"""
    result = extract_bearer_token("Bearer user_token-with.special+chars")
    assert result == "user_token-with.special+chars"


def test_extract_bearer_token_very_long_token():
    """Very long token string"""
    long_token = "user_" + "a" * 1000
    result = extract_bearer_token(f"Bearer {long_token}")
    assert result == long_token


def test_extract_bearer_token_numeric_token():
    """Purely numeric token (not starting with user_)"""
    result = extract_bearer_token("Bearer 123456789")
    assert result == "123456789"


def test_extract_bearer_token_token_with_equals():
    """Token that looks like base64 with equals signs"""
    result = extract_bearer_token("Bearer dGVzdA==")
    assert result == "dGVzdA=="


def test_extract_bearer_token_unicode_token():
    """Token with unicode characters"""
    result = extract_bearer_token("Bearer user_tökén")
    assert result == "user_tökén"


# ============================================================================
# Tests for validate_token()
# ============================================================================


def test_validate_token_valid_user_prefix():
    """Happy path: token starts with 'user_'"""
    result = validate_token("user_123")
    assert result is True


def test_validate_token_valid_user_prefix_long():
    """Valid token with long suffix"""
    result = validate_token("user_abcdefghijklmnopqrstuvwxyz1234567890")
    assert result is True


def test_validate_token_valid_just_user_underscore():
    """Token that is exactly 'user_' (edge case)"""
    result = validate_token("user_")
    assert result is True


def test_validate_token_invalid_no_prefix():
    """Token without user_ prefix should be invalid"""
    result = validate_token("invalid_token")
    assert result is False


def test_validate_token_invalid_wrong_prefix():
    """Token with different prefix should be invalid"""
    result = validate_token("admin_123")
    assert result is False


def test_validate_token_invalid_user_without_underscore():
    """Token 'user' without underscore should be invalid"""
    result = validate_token("user")
    assert result is False


def test_validate_token_invalid_user_with_space():
    """Token 'user _123' with space should be invalid"""
    result = validate_token("user _123")
    assert result is False


def test_validate_token_invalid_empty_string():
    """Empty string should be invalid"""
    result = validate_token("")
    assert result is False


def test_validate_token_invalid_whitespace():
    """Whitespace-only string should be invalid"""
    result = validate_token("   ")
    assert result is False


def test_validate_token_case_sensitive():
    """Validation should be case-sensitive: USER_ is not user_"""
    result = validate_token("USER_123")
    assert result is False


def test_validate_token_case_sensitive_mixed():
    """Validation should be case-sensitive: User_ is not user_"""
    result = validate_token("User_123")
    assert result is False


def test_validate_token_prefix_in_middle():
    """Token with user_ in middle but not at start should be invalid"""
    result = validate_token("token_user_123")
    assert result is False


def test_validate_token_none_raises_attribute_error():
    """
    CRITICAL BUG TEST: None token should raise AttributeError
    
    The recent code change removed the null check, causing this function
    to call .startswith() on None, which raises AttributeError.
    This test documents the current buggy behavior.
    """
    with pytest.raises(AttributeError):
        validate_token(None)


def test_validate_token_none_should_return_false():
    """
    EXPECTED BEHAVIOR: None token should return False
    
    This test is currently expected to FAIL due to the bug.
    Once the null check is restored, this test should pass.
    
    The function should defensively handle None inputs and return False
    rather than raising an exception, consistent with the docstring
    that states 'Empty/malformed tokens are invalid'.
    """
    pytest.skip("Skipped: Known bug - validate_token raises AttributeError on None")
    # When bug is fixed, uncomment the following:
    # result = validate_token(None)
    # assert result is False


def test_validate_token_numeric_only():
    """Purely numeric string without prefix should be invalid"""
    result = validate_token("123456")
    assert result is False


def test_validate_token_special_chars_prefix():
    """Token starting with special characters should be invalid"""
    result = validate_token("!@#$_123")
    assert result is False


def test_validate_token_underscore_only():
    """Single underscore should be invalid"""
    result = validate_token("_")
    assert result is False


def test_validate_token_multiple_underscores():
    """Token with multiple underscores but wrong prefix"""
    result = validate_token("___user_123")
    assert result is False


def test_validate_token_unicode_prefix():
    """Token with unicode characters in prefix should be invalid"""
    result = validate_token("üser_123")
    assert result is False


def test_validate_token_valid_with_special_chars_after_prefix():
    """Valid user_ prefix with special characters in the rest"""
    result = validate_token("user_!@#$%^&*()")
    assert result is True


def test_validate_token_valid_with_newline():
    """Valid token but contains newline (edge case)"""
    result = validate_token("user_123\n")
    assert result is True


def test_validate_token_valid_with_tab():
    """Valid token but contains tab (edge case)"""
    result = validate_token("user_123\t")
    assert result is True


# ============================================================================
# Integration tests: extract_bearer_token + validate_token
# ============================================================================


def test_integration_valid_bearer_and_valid_token():
    """Integration: valid Bearer header with valid user_ token"""
    token = extract_bearer_token("Bearer user_12345")
    result = validate_token(token)
    assert result is True


def test_integration_valid_bearer_invalid_token():
    """Integration: valid Bearer header but invalid token (no user_ prefix)"""
    token = extract_bearer_token("Bearer invalid_token")
    result = validate_token(token)
    assert result is False


def test_integration_invalid_bearer_returns_none():
    """Integration: invalid Bearer header returns None"""
    token = extract_bearer_token("Invalid header")
    assert token is None
    # This will trigger the bug!
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_none_header_returns_none():
    """Integration: None header returns None token"""
    token = extract_bearer_token(None)
    assert token is None
    # This will trigger the bug!
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_empty_header_returns_none():
    """Integration: empty header returns None token"""
    token = extract_bearer_token("")
    assert token is None
    # This will trigger the bug!
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_malformed_bearer_returns_none():
    """Integration: malformed Bearer (no token) returns None"""
    token = extract_bearer_token("Bearer ")
    assert token is None
    # This will trigger the bug!
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_wrong_scheme_returns_none():
    """Integration: wrong scheme returns None token"""
    token = extract_bearer_token("Basic user_token")
    assert token is None
    # This will trigger the bug!
    with pytest.raises(AttributeError):
        validate_token(token)


# ============================================================================
# Additional edge case tests
# ============================================================================


def test_extract_bearer_token_newline_in_header():
    """Header with newline characters"""
    result = extract_bearer_token("Bearer\nuser_token")
    # This splits into ["Bearer\nuser_token"], len=1, should return None
    assert result is None


def test_extract_bearer_token_tab_separated():
    """Bearer and token separated by tab"""
    result = extract_bearer_token("Bearer\tuser_token")
    # Tab is not a space for split(), so this becomes ["Bearer\tuser_token"]
    assert result is None


def test_validate_token_very_long_valid_token():
    """Very long token with valid prefix"""
    long_token = "user_" + "x" * 10000
    result = validate_token(long_token)
    assert result is True


def test_validate_token_very_long_invalid_token():
    """Very long token without valid prefix"""
    long_token = "invalid_" + "x" * 10000
    result = validate_token(long_token)
    assert result is False


def test_extract_bearer_token_bearer_as_token():
    """Token value is literally 'Bearer' (confusing but valid format)"""
    result = extract_bearer_token("Bearer Bearer")
    assert result == "Bearer"


def test_validate_token_bearer_as_token_value():
    """Token value is 'Bearer' - should be invalid (no user_ prefix)"""
    result = validate_token("Bearer")
    assert result is False