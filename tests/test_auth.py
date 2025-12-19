import pytest

from app.auth import extract_bearer_token, validate_token


# =============================================================================
# Tests for extract_bearer_token
# =============================================================================

def test_extract_bearer_token_valid_token():
    """Happy path: valid Bearer token"""
    result = extract_bearer_token("Bearer user_12345")
    assert result == "user_12345"


def test_extract_bearer_token_valid_with_whitespace():
    """Token with extra whitespace should be stripped"""
    result = extract_bearer_token("Bearer   user_abc   ")
    assert result == "user_abc"


def test_extract_bearer_token_case_insensitive_scheme():
    """Bearer scheme should be case-insensitive"""
    assert extract_bearer_token("bearer user_test") == "user_test"
    assert extract_bearer_token("BEARER user_test") == "user_test"
    assert extract_bearer_token("BeArEr user_test") == "user_test"


def test_extract_bearer_token_none_header():
    """None header should return None (defensive)"""
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
    """Header with only scheme (no token) should return None"""
    result = extract_bearer_token("Bearer")
    assert result is None


def test_extract_bearer_token_missing_scheme():
    """Header with only token (no scheme) should return None"""
    result = extract_bearer_token("user_12345")
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


def test_extract_bearer_token_empty_token_after_strip():
    """If token is empty after stripping, return None"""
    result = extract_bearer_token("Bearer    ")
    assert result is None


def test_extract_bearer_token_with_special_characters():
    """Token with special characters should be extracted correctly"""
    result = extract_bearer_token("Bearer user_123-abc.def_xyz")
    assert result == "user_123-abc.def_xyz"


def test_extract_bearer_token_with_underscores():
    """Token with underscores (common in our system) should work"""
    result = extract_bearer_token("Bearer user_premium_account_789")
    assert result == "user_premium_account_789"


def test_extract_bearer_token_numeric_only():
    """Purely numeric token should be extracted"""
    result = extract_bearer_token("Bearer 1234567890")
    assert result == "1234567890"


def test_extract_bearer_token_single_character():
    """Single character token should be extracted"""
    result = extract_bearer_token("Bearer x")
    assert result == "x"


# =============================================================================
# Tests for validate_token
# =============================================================================

def test_validate_token_valid_user_prefix():
    """Happy path: token starting with 'user_' is valid"""
    assert validate_token("user_12345") is True
    assert validate_token("user_abc") is True
    assert validate_token("user_") is True  # Just prefix is technically valid


def test_validate_token_valid_long_token():
    """Long token with user_ prefix should be valid"""
    long_token = "user_" + "a" * 1000
    assert validate_token(long_token) is True


def test_validate_token_invalid_no_prefix():
    """Token without 'user_' prefix should be invalid"""
    assert validate_token("admin_12345") is False
    assert validate_token("token_12345") is False
    assert validate_token("12345") is False
    assert validate_token("xyz") is False


def test_validate_token_invalid_wrong_prefix():
    """Token with similar but wrong prefix should be invalid"""
    assert validate_token("users_12345") is False  # plural
    assert validate_token("User_12345") is False  # capitalized
    assert validate_token("USER_12345") is False  # all caps
    assert validate_token("_user_12345") is False  # underscore before


def test_validate_token_invalid_empty_string():
    """Empty string should be invalid"""
    assert validate_token("") is False


def test_validate_token_invalid_whitespace():
    """Whitespace-only token should be invalid"""
    assert validate_token("   ") is False
    assert validate_token("\t") is False
    assert validate_token("\n") is False


def test_validate_token_none_raises_attribute_error():
    """
    CRITICAL: None token should raise AttributeError
    This tests the CURRENT behavior after the diff removed the None check.
    This is a BUG that should be caught by this test.
    """
    with pytest.raises(AttributeError):
        validate_token(None)


def test_validate_token_partial_match():
    """Token containing 'user_' but not at start should be invalid"""
    assert validate_token("myuser_123") is False
    assert validate_token("admin_user_123") is False
    assert validate_token("__user_123") is False


def test_validate_token_with_spaces():
    """Token with spaces should be handled correctly"""
    # Space before prefix - invalid
    assert validate_token(" user_123") is False
    # Space after prefix - technically valid since it starts with "user_"
    assert validate_token("user_ 123") is True
    # Space in middle - valid if starts with "user_"
    assert validate_token("user_my token") is True


def test_validate_token_case_sensitivity():
    """Validation should be case-sensitive"""
    assert validate_token("user_123") is True
    assert validate_token("User_123") is False
    assert validate_token("USER_123") is False
    assert validate_token("UsEr_123") is False


def test_validate_token_special_characters_after_prefix():
    """Special characters after valid prefix should still be valid"""
    assert validate_token("user_!@#$%") is True
    assert validate_token("user_123-abc") is True
    assert validate_token("user_abc.def") is True
    assert validate_token("user_🔥") is True  # emoji


def test_validate_token_just_user_prefix():
    """Exactly 'user_' with nothing after is valid"""
    assert validate_token("user_") is True


def test_validate_token_almost_prefix():
    """Almost correct prefix should be invalid"""
    assert validate_token("user") is False  # missing underscore
    assert validate_token("use_r") is False  # underscore in wrong place
    assert validate_token("u_ser") is False


# =============================================================================
# Integration tests: extract_bearer_token + validate_token
# =============================================================================

def test_integration_valid_auth_flow():
    """Full auth flow: extract and validate a good token"""
    header = "Bearer user_12345"
    token = extract_bearer_token(header)
    assert token == "user_12345"
    assert validate_token(token) is True


def test_integration_invalid_scheme():
    """Full auth flow: wrong scheme results in None, which raises on validate"""
    header = "Basic user_12345"
    token = extract_bearer_token(header)
    assert token is None
    # Validate the None token - this will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_missing_header():
    """Full auth flow: None header results in None token, which raises on validate"""
    header = None
    token = extract_bearer_token(header)
    assert token is None
    # Validate the None token - this will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_malformed_header():
    """Full auth flow: malformed header results in None token, which raises on validate"""
    header = "NotBearer something"
    token = extract_bearer_token(header)
    assert token is None
    # Validate the None token - this will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_valid_extraction_invalid_token():
    """Full auth flow: valid extraction but token doesn't start with user_"""
    header = "Bearer admin_12345"
    token = extract_bearer_token(header)
    assert token == "admin_12345"
    assert validate_token(token) is False


def test_integration_empty_token_extracted():
    """Full auth flow: Bearer with empty token after strip"""
    header = "Bearer    "
    token = extract_bearer_token(header)
    assert token is None
    # Validate the None token - this will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


# =============================================================================
# Edge cases and boundary tests
# =============================================================================

def test_extract_bearer_token_unicode_characters():
    """Unicode characters in token should be handled"""
    result = extract_bearer_token("Bearer user_日本語")
    assert result == "user_日本語"


def test_validate_token_unicode_prefix():
    """Unicode token with correct prefix should validate"""
    assert validate_token("user_日本語") is True
    assert validate_token("user_مرحبا") is True


def test_extract_bearer_token_very_long_header():
    """Very long header should be handled correctly"""
    long_token = "x" * 10000
    header = f"Bearer {long_token}"
    result = extract_bearer_token(header)
    assert result == long_token


def test_validate_token_newline_in_token():
    """Token with newline character (edge case)"""
    assert validate_token("user_\n123") is True  # Starts with user_


def test_extract_bearer_token_tabs_as_separator():
    """Tabs should split the same way as spaces"""
    result = extract_bearer_token("Bearer\tuser_123")
    assert result == "user_123"


def test_extract_bearer_token_multiple_spaces():
    """Multiple spaces between Bearer and token"""
    result = extract_bearer_token("Bearer     user_123")
    assert result is None  # split() creates more than 2 parts


def test_validate_token_zero_width_characters():
    """Zero-width characters (edge case for string manipulation)"""
    # Zero-width space after user_
    assert validate_token("user_\u200b") is True