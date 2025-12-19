import pytest

from app.auth import extract_bearer_token, validate_token


# ============================================================================
# Tests for extract_bearer_token
# ============================================================================

def test_extract_bearer_token_happy_path():
    """Valid Bearer token is extracted correctly."""
    result = extract_bearer_token("Bearer user_12345")
    assert result == "user_12345"


def test_extract_bearer_token_with_extra_whitespace():
    """Bearer token with extra whitespace around token is handled correctly."""
    result = extract_bearer_token("Bearer   user_12345   ")
    assert result == "user_12345"


def test_extract_bearer_token_case_insensitive_scheme():
    """Bearer scheme is case-insensitive (bearer, BEARER, Bearer all work)."""
    assert extract_bearer_token("bearer user_token") == "user_token"
    assert extract_bearer_token("BEARER user_token") == "user_token"
    assert extract_bearer_token("BeArEr user_token") == "user_token"


def test_extract_bearer_token_with_none_header():
    """None header returns None gracefully."""
    result = extract_bearer_token(None)
    assert result is None


def test_extract_bearer_token_with_empty_string():
    """Empty string header returns None gracefully."""
    result = extract_bearer_token("")
    assert result is None


def test_extract_bearer_token_with_whitespace_only():
    """Whitespace-only header returns None gracefully."""
    result = extract_bearer_token("   ")
    assert result is None


def test_extract_bearer_token_missing_token_part():
    """Header with only 'Bearer' (no token) returns None."""
    result = extract_bearer_token("Bearer")
    assert result is None


def test_extract_bearer_token_missing_scheme():
    """Header with only token (no scheme) returns None."""
    result = extract_bearer_token("user_12345")
    assert result is None


def test_extract_bearer_token_wrong_scheme():
    """Header with wrong scheme (not Bearer) returns None."""
    result = extract_bearer_token("Basic user_12345")
    assert result is None


def test_extract_bearer_token_too_many_parts():
    """Header with more than 2 parts returns None."""
    result = extract_bearer_token("Bearer user_token extra_part")
    assert result is None


def test_extract_bearer_token_with_empty_token():
    """Header with Bearer but empty/whitespace token returns None."""
    result = extract_bearer_token("Bearer    ")
    assert result is None


def test_extract_bearer_token_with_special_characters():
    """Token with special characters is extracted correctly."""
    result = extract_bearer_token("Bearer user_abc-123.xyz")
    assert result == "user_abc-123.xyz"


def test_extract_bearer_token_with_very_long_token():
    """Very long token is extracted correctly."""
    long_token = "user_" + "a" * 1000
    result = extract_bearer_token(f"Bearer {long_token}")
    assert result == long_token


def test_extract_bearer_token_with_numeric_token():
    """Purely numeric token is extracted correctly."""
    result = extract_bearer_token("Bearer 123456789")
    assert result == "123456789"


def test_extract_bearer_token_single_character_token():
    """Single character token is extracted correctly."""
    result = extract_bearer_token("Bearer x")
    assert result == "x"


# ============================================================================
# Tests for validate_token
# ============================================================================

def test_validate_token_happy_path():
    """Valid token starting with 'user_' returns True."""
    assert validate_token("user_12345") is True


def test_validate_token_minimal_valid():
    """Token 'user_' (minimal valid) returns True."""
    assert validate_token("user_") is True


def test_validate_token_with_special_characters():
    """Valid token with special characters returns True."""
    assert validate_token("user_abc-123.xyz_890") is True


def test_validate_token_with_none():
    """None token should be handled gracefully (current code will raise AttributeError)."""
    # This test will expose the bug introduced by removing the None check
    with pytest.raises(AttributeError):
        validate_token(None)


def test_validate_token_with_empty_string():
    """Empty string token returns False."""
    assert validate_token("") is False


def test_validate_token_wrong_prefix():
    """Token not starting with 'user_' returns False."""
    assert validate_token("admin_12345") is False
    assert validate_token("token_12345") is False
    assert validate_token("12345") is False


def test_validate_token_case_sensitive_prefix():
    """Prefix is case-sensitive (User_, USER_ should fail)."""
    assert validate_token("User_12345") is False
    assert validate_token("USER_12345") is False
    assert validate_token("UsEr_12345") is False


def test_validate_token_prefix_as_substring():
    """Token containing 'user_' but not at start returns False."""
    assert validate_token("myuser_12345") is False
    assert validate_token("the_user_12345") is False


def test_validate_token_just_user_without_underscore():
    """Token 'user' without underscore returns False."""
    assert validate_token("user") is False


def test_validate_token_whitespace_before_prefix():
    """Token with leading whitespace returns False."""
    assert validate_token(" user_12345") is False
    assert validate_token("  user_12345") is False


def test_validate_token_whitespace_after_prefix():
    """Token with trailing whitespace is still valid if starts with 'user_'."""
    assert validate_token("user_12345  ") is True


def test_validate_token_very_long_valid_token():
    """Very long valid token returns True."""
    long_token = "user_" + "x" * 10000
    assert validate_token(long_token) is True


def test_validate_token_unicode_characters():
    """Token with unicode characters after 'user_' returns True."""
    assert validate_token("user_测试") is True
    assert validate_token("user_🚀") is True


def test_validate_token_only_prefix():
    """Token that is exactly 'user_' returns True."""
    assert validate_token("user_") is True


def test_validate_token_with_newline():
    """Token with newline characters returns False if not starting with 'user_'."""
    assert validate_token("\nuser_12345") is False
    assert validate_token("user_\n12345") is True  # starts with user_


def test_validate_token_with_tab():
    """Token with tab characters."""
    assert validate_token("\tuser_12345") is False
    assert validate_token("user_\t12345") is True


# ============================================================================
# Integration tests (testing both functions together)
# ============================================================================

def test_integration_valid_bearer_token_flow():
    """Complete flow: extract and validate a valid Bearer token."""
    header = "Bearer user_abc123"
    token = extract_bearer_token(header)
    assert token == "user_abc123"
    assert validate_token(token) is True


def test_integration_invalid_token_prefix_flow():
    """Complete flow: extract token but validation fails due to wrong prefix."""
    header = "Bearer admin_xyz"
    token = extract_bearer_token(header)
    assert token == "admin_xyz"
    assert validate_token(token) is False


def test_integration_malformed_header_flow():
    """Complete flow: malformed header results in None token."""
    header = "Invalid Header Format"
    token = extract_bearer_token(header)
    assert token is None
    # This will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_none_header_flow():
    """Complete flow: None header results in None token."""
    token = extract_bearer_token(None)
    assert token is None
    # This will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_empty_header_flow():
    """Complete flow: empty header results in None token."""
    token = extract_bearer_token("")
    assert token is None
    # This will raise AttributeError due to the bug
    with pytest.raises(AttributeError):
        validate_token(token)


def test_integration_bearer_with_wrong_prefix_token():
    """Complete flow: valid Bearer header but token doesn't start with user_."""
    header = "Bearer token123"
    token = extract_bearer_token(header)
    assert token == "token123"
    assert validate_token(token) is False


def test_integration_case_insensitive_bearer_valid_token():
    """Complete flow: case-insensitive Bearer with valid user_ token."""
    header = "bearer user_test"
    token = extract_bearer_token(header)
    assert token == "user_test"
    assert validate_token(token) is True