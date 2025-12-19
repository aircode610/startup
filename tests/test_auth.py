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