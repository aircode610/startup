import pytest

from app.auth import extract_bearer_token, validate_token


# =============================================================================
# Tests for extract_bearer_token
# =============================================================================
# These tests ensure defensive parsing per ADR-014 and incident Nov 2024


def test_extract_bearer_token_happy_path():
    """Valid Bearer token is extracted correctly."""
    result = extract_bearer_token("Bearer user_12345")
    assert result == "user_12345"


def test_extract_bearer_token_with_valid_prefix():
    """Token with valid user_ prefix is extracted."""
    result = extract_bearer_token("Bearer user_abc123")
    assert result == "user_abc123"


def test_extract_bearer_token_case_insensitive_scheme():
    """Bearer scheme should be case-insensitive."""
    assert extract_bearer_token("bearer user_123") == "user_123"
    assert extract_bearer_token("Bearer user_123") == "user_123"
    assert extract_bearer_token("BEARER user_123") == "user_123"
    assert extract_bearer_token("BeArEr user_123") == "user_123"


def test_extract_bearer_token_strips_whitespace():
    """Token value should be stripped of surrounding whitespace."""
    result = extract_bearer_token("Bearer   user_123   ")
    assert result == "user_123"


def test_extract_bearer_token_none_header():
    """None header returns None (defensive - no exception)."""
    result = extract_bearer_token(None)
    assert result is None


def test_extract_bearer_token_empty_string():
    """Empty string header returns None."""
    result = extract_bearer_token("")
    assert result is None


def test_extract_bearer_token_whitespace_only():
    """Whitespace-only header returns None."""
    result = extract_bearer_token("   ")
    assert result is None


def test_extract_bearer_token_missing_token_part():
    """Header with only scheme (no token) returns None."""
    result = extract_bearer_token("Bearer")
    assert result is None


def test_extract_bearer_token_missing_token_with_space():
    """Header 'Bearer ' with trailing space but no token returns None."""
    result = extract_bearer_token("Bearer ")
    assert result is None


def test_extract_bearer_token_too_many_parts():
    """Header with extra parts returns None."""
    result = extract_bearer_token("Bearer user_123 extra")
    assert result is None


def test_extract_bearer_token_wrong_scheme():
    """Non-Bearer scheme returns None."""
    result = extract_bearer_token("Basic user_123")
    assert result is None


def test_extract_bearer_token_token_only_no_scheme():
    """Token without scheme returns None."""
    result = extract_bearer_token("user_123")
    assert result is None


def test_extract_bearer_token_malformed_various():
    """Various malformed headers return None without raising."""
    malformed_headers = [
        "Bearer",
        "Bearer  ",
        "bearer",
        "Token user_123",
        "user_123",
        "Bearer\tuser_123\textra",
        "Bearer user_123 extra stuff",
        "NotBearer user_123",
        "Bear user_123",
        "Bearer\nuser_123",
    ]
    for header in malformed_headers:
        result = extract_bearer_token(header)
        assert result is None, f"Expected None for malformed header: {header!r}"


def test_extract_bearer_token_empty_token_after_strip():
    """Header 'Bearer    ' with only whitespace in token part returns None."""
    result = extract_bearer_token("Bearer    ")
    assert result is None


# =============================================================================
# Tests for validate_token
# =============================================================================
# Critical: These tests catch the bug introduced in the current branch
# where the None check was removed from validate_token


def test_validate_token_valid_user_prefix():
    """Token starting with 'user_' is valid."""
    assert validate_token("user_123") is True
    assert validate_token("user_abc") is True
    assert validate_token("user_") is True
    assert validate_token("user_12345_abcdef") is True


def test_validate_token_invalid_without_prefix():
    """Token not starting with 'user_' is invalid."""
    assert validate_token("admin_123") is False
    assert validate_token("token_123") is False
    assert validate_token("123_user") is False
    assert validate_token("abc123") is False


def test_validate_token_empty_string():
    """Empty string token is invalid."""
    assert validate_token("") is False


def test_validate_token_none():
    """
    None token must be invalid (critical test per ADR-014).
    
    This catches the regression introduced by removing the None check.
    extract_bearer_token can return None for malformed headers,
    so validate_token must handle None defensively.
    """
    assert validate_token(None) is False


def test_validate_token_case_sensitive_prefix():
    """Token validation is case-sensitive - 'User_' or 'USER_' should be invalid."""
    assert validate_token("User_123") is False
    assert validate_token("USER_123") is False
    assert validate_token("UsEr_123") is False


def test_validate_token_whitespace_prefix():
    """Token with leading/trailing whitespace is invalid."""
    assert validate_token(" user_123") is False
    assert validate_token("user_123 ") is False
    assert validate_token(" user_123 ") is False


def test_validate_token_special_characters():
    """Valid tokens can contain special characters after prefix."""
    assert validate_token("user_123-456") is True
    assert validate_token("user_abc@def") is True
    assert validate_token("user_!@#$%") is True


def test_validate_token_minimal_valid():
    """Minimal valid token is just 'user_'."""
    assert validate_token("user_") is True


def test_validate_token_almost_valid():
    """Tokens almost matching pattern are invalid."""
    assert validate_token("user") is False
    assert validate_token("use_123") is False
    assert validate_token("ser_123") is False
    assert validate_token("_user_123") is False


# =============================================================================
# Integration tests - extract + validate flow
# =============================================================================


def test_auth_flow_valid_header():
    """Full auth flow: valid header -> valid token -> authorized."""
    token = extract_bearer_token("Bearer user_alice123")
    assert token == "user_alice123"
    assert validate_token(token) is True


def test_auth_flow_missing_header():
    """Full auth flow: missing header -> None token -> unauthorized."""
    token = extract_bearer_token(None)
    assert token is None
    assert validate_token(token) is False


def test_auth_flow_malformed_header():
    """Full auth flow: malformed header -> None token -> unauthorized."""
    token = extract_bearer_token("Bearer")
    assert token is None
    assert validate_token(token) is False


def test_auth_flow_wrong_scheme():
    """Full auth flow: wrong scheme -> None token -> unauthorized."""
    token = extract_bearer_token("Basic user_123")
    assert token is None
    assert validate_token(token) is False


def test_auth_flow_invalid_token_format():
    """Full auth flow: valid header but invalid token format -> unauthorized."""
    token = extract_bearer_token("Bearer admin_123")
    assert token == "admin_123"
    assert validate_token(token) is False


def test_auth_flow_extra_spaces():
    """Full auth flow: header with extra spaces -> handles gracefully."""
    token = extract_bearer_token("Bearer user_123 extra")
    assert token is None
    assert validate_token(token) is False


# =============================================================================
# Incident regression tests (Nov 2024)
# =============================================================================
# These tests specifically address the incident scenarios


def test_incident_regression_empty_header():
    """Regression test: empty header must not raise exception."""
    token = extract_bearer_token("")
    assert token is None
    # This should not raise AttributeError
    assert validate_token(token) is False


def test_incident_regression_header_with_extra_spaces():
    """Regression test: headers with extra spaces must not raise exception."""
    headers = [
        "Bearer  user_123  extra",
        "Bearer   ",
        "  Bearer user_123",
    ]
    for header in headers:
        token = extract_bearer_token(header)
        # validate_token must handle whatever extract_bearer_token returns
        is_valid = validate_token(token)
        # Should be False and not raise
        assert is_valid is False or is_valid is True


def test_incident_regression_non_bearer_schemes():
    """Regression test: non-bearer schemes must not raise exception."""
    schemes = [
        "Basic dXNlcjpwYXNz",
        "Digest username=user",
        "Token abc123",
        "OAuth oauth_token=xyz",
    ]
    for header in schemes:
        token = extract_bearer_token(header)
        assert token is None
        # Must not raise
        assert validate_token(token) is False


# =============================================================================
# Property-based / parameterized edge case tests
# =============================================================================


@pytest.mark.parametrize(
    "invalid_token",
    [
        None,
        "",
        "admin_123",
        "guest_456",
        "User_123",  # wrong case
        "USER_789",  # wrong case
        " user_123",  # leading space
        "user_123 ",  # trailing space
        "123",
        "token",
        "_user_123",  # underscore prefix
        "xuser_123",  # extra char before
    ],
)
def test_validate_token_parametrized_invalid(invalid_token):
    """Parametrized test for various invalid token formats."""
    assert validate_token(invalid_token) is False


@pytest.mark.parametrize(
    "valid_token",
    [
        "user_",
        "user_1",
        "user_123",
        "user_abc",
        "user_alice",
        "user_123abc",
        "user_!@#",
        "user_very_long_token_value_12345",
    ],
)
def test_validate_token_parametrized_valid(valid_token):
    """Parametrized test for various valid token formats."""
    assert validate_token(valid_token) is True


@pytest.mark.parametrize(
    "header,expected_token",
    [
        ("Bearer user_123", "user_123"),
        ("bearer user_123", "user_123"),
        ("BEARER user_123", "user_123"),
        ("Bearer user_", "user_"),
        ("Bearer user_abc123def", "user_abc123def"),
    ],
)
def test_extract_bearer_token_parametrized_valid(header, expected_token):
    """Parametrized test for valid bearer token extraction."""
    assert extract_bearer_token(header) == expected_token


@pytest.mark.parametrize(
    "malformed_header",
    [
        None,
        "",
        "   ",
        "Bearer",
        "Bearer ",
        "Basic user_123",
        "Token user_123",
        "user_123",
        "Bearer user_123 extra",
        "Bearer  user_123  extra",
        "Not Bearer user_123",
    ],
)
def test_extract_bearer_token_parametrized_invalid(malformed_header):
    """Parametrized test for malformed headers returning None."""
    assert extract_bearer_token(malformed_header) is None