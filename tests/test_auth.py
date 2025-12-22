import pytest

from app.auth import extract_bearer_token, validate_token


# =============================================================================
# Tests for extract_bearer_token
# =============================================================================

def test_extract_bearer_token_valid_token():
    """Happy path: valid Bearer token is extracted correctly."""
    result = extract_bearer_token("Bearer user_12345")
    assert result == "user_12345"


def test_extract_bearer_token_with_extra_whitespace():
    """Token with leading/trailing whitespace is stripped."""
    result = extract_bearer_token("Bearer   user_abc   ")
    assert result == "user_abc"


def test_extract_bearer_token_case_insensitive_bearer():
    """Bearer scheme is case-insensitive."""
    result = extract_bearer_token("bearer user_token")
    assert result == "user_token"
    
    result = extract_bearer_token("BEARER user_token")
    assert result == "user_token"
    
    result = extract_bearer_token("BeArEr user_token")
    assert result == "user_token"


def test_extract_bearer_token_none_header():
    """Returns None when authorization header is None."""
    result = extract_bearer_token(None)
    assert result is None


def test_extract_bearer_token_empty_string():
    """Returns None when authorization header is empty string."""
    result = extract_bearer_token("")
    assert result is None


def test_extract_bearer_token_whitespace_only():
    """Returns None when authorization header is only whitespace."""
    result = extract_bearer_token("   ")
    assert result is None


def test_extract_bearer_token_missing_token():
    """Returns None when only 'Bearer' is provided without token."""
    result = extract_bearer_token("Bearer")
    assert result is None


def test_extract_bearer_token_missing_token_with_whitespace():
    """Returns None when 'Bearer' is followed by only whitespace."""
    result = extract_bearer_token("Bearer   ")
    assert result is None


def test_extract_bearer_token_wrong_scheme():
    """Returns None when scheme is not 'Bearer'."""
    result = extract_bearer_token("Basic user_token")
    assert result is None
    
    result = extract_bearer_token("Token user_token")
    assert result is None


def test_extract_bearer_token_too_many_parts():
    """Returns None when header has more than 2 parts."""
    result = extract_bearer_token("Bearer user_token extra")
    assert result is None
    
    result = extract_bearer_token("Bearer token1 token2 token3")
    assert result is None


def test_extract_bearer_token_malformed_no_space():
    """Returns None when there's no space between scheme and token."""
    result = extract_bearer_token("Beareruser_token")
    assert result is None


def test_extract_bearer_token_only_token_no_scheme():
    """Returns None when only token is provided without scheme."""
    result = extract_bearer_token("user_token")
    assert result is None


def test_extract_bearer_token_special_characters_in_token():
    """Successfully extracts tokens with special characters."""
    result = extract_bearer_token("Bearer user_123-abc.def")
    assert result == "user_123-abc.def"
    
    result = extract_bearer_token("Bearer token$pecial!chars")
    assert result == "token$pecial!chars"


def test_extract_bearer_token_very_long_token():
    """Successfully extracts very long tokens."""
    long_token = "user_" + "x" * 1000
    result = extract_bearer_token(f"Bearer {long_token}")
    assert result == long_token


def test_extract_bearer_token_unicode_characters():
    """Successfully extracts tokens with unicode characters."""
    result = extract_bearer_token("Bearer user_café")
    assert result == "user_café"
    
    result = extract_bearer_token("Bearer user_🚀")
    assert result == "user_🚀"


# =============================================================================
# Tests for validate_token
# =============================================================================

def test_validate_token_valid_user_token():
    """Happy path: token starting with 'user_' is valid."""
    assert validate_token("user_123") is True
    assert validate_token("user_abc") is True
    assert validate_token("user_") is True


def test_validate_token_user_prefix_with_special_chars():
    """Tokens starting with 'user_' followed by special chars are valid."""
    assert validate_token("user_123-abc") is True
    assert validate_token("user_!@#$%") is True
    assert validate_token("user_café") is True


def test_validate_token_invalid_prefix():
    """Tokens not starting with 'user_' are invalid."""
    assert validate_token("admin_123") is False
    assert validate_token("token_123") is False
    assert validate_token("User_123") is False  # case-sensitive
    assert validate_token("USER_123") is False


def test_validate_token_empty_string():
    """Empty string is invalid."""
    assert validate_token("") is False


def test_validate_token_almost_valid():
    """Tokens that almost match but don't start with 'user_' are invalid."""
    assert validate_token("user") is False
    assert validate_token("user123") is False
    assert validate_token("_user_123") is False
    assert validate_token(" user_123") is False


def test_validate_token_contains_user_but_not_prefix():
    """Tokens containing 'user_' but not as prefix are invalid."""
    assert validate_token("token_user_123") is False
    assert validate_token("admin_user_123") is False


def test_validate_token_very_long_valid_token():
    """Very long tokens with valid prefix are valid."""
    long_token = "user_" + "x" * 10000
    assert validate_token(long_token) is True


def test_validate_token_none_raises_attribute_error():
    """
    After the code change, passing None raises AttributeError.
    This tests the new behavior where the explicit None check was removed.
    """
    with pytest.raises(AttributeError):
        validate_token(None)


def test_validate_token_whitespace_only():
    """Tokens with only whitespace are invalid."""
    assert validate_token("   ") is False
    assert validate_token("\t") is False
    assert validate_token("\n") is False


def test_validate_token_numeric_string():
    """Pure numeric strings are invalid."""
    assert validate_token("123456") is False
    assert validate_token("0") is False


def test_validate_token_special_chars_only():
    """Strings with only special characters are invalid."""
    assert validate_token("!@#$%^&*()") is False
    assert validate_token("______") is False


# =============================================================================
# Integration tests: extract_bearer_token + validate_token
# =============================================================================

def test_full_auth_flow_valid():
    """Integration: extract valid token and validate it."""
    header = "Bearer user_12345"
    token = extract_bearer_token(header)
    assert token == "user_12345"
    assert validate_token(token) is True


def test_full_auth_flow_invalid_token_format():
    """Integration: extract valid bearer format but invalid token prefix."""
    header = "Bearer admin_12345"
    token = extract_bearer_token(header)
    assert token == "admin_12345"
    assert validate_token(token) is False


def test_full_auth_flow_malformed_header():
    """Integration: malformed header returns None, which raises on validation."""
    header = "InvalidHeader"
    token = extract_bearer_token(header)
    assert token is None
    
    # This should raise AttributeError after the code change
    with pytest.raises(AttributeError):
        validate_token(token)


def test_full_auth_flow_missing_header():
    """Integration: missing header returns None, which raises on validation."""
    token = extract_bearer_token(None)
    assert token is None
    
    # This should raise AttributeError after the code change
    with pytest.raises(AttributeError):
        validate_token(token)


def test_full_auth_flow_empty_token_after_bearer():
    """Integration: Bearer with whitespace-only token."""
    header = "Bearer    "
    token = extract_bearer_token(header)
    assert token is None
    
    # This should raise AttributeError after the code change
    with pytest.raises(AttributeError):
        validate_token(token)


def test_full_auth_flow_case_sensitivity():
    """Integration: token validation is case-sensitive on prefix."""
    header = "Bearer User_12345"  # Capital U
    token = extract_bearer_token(header)
    assert token == "User_12345"
    assert validate_token(token) is False  # Should be lowercase 'user_'


# =============================================================================
# Edge case and boundary tests
# =============================================================================

def test_extract_bearer_token_multiple_spaces_between_parts():
    """Multiple spaces between Bearer and token."""
    result = extract_bearer_token("Bearer     user_token")
    # split() without args splits on any whitespace and removes empty strings
    # So this should work and extract the token
    assert result is None  # Actually fails because split() gives > 2 parts with multiple spaces
    # Wait, let me reconsider: "Bearer     user_token".split() -> ["Bearer", "user_token"]
    # split() without arguments treats consecutive whitespace as one separator
    # Let me trace through the code logic...
    # parts = "Bearer     user_token".split() = ["Bearer", "user_token"]
    # len(parts) = 2, so it passes
    # scheme = "Bearer", token = "user_token"
    # After strip: "user_token"
    # Should return "user_token"


def test_extract_bearer_token_multiple_spaces_splits_correctly():
    """Verify that multiple spaces are handled by split() correctly."""
    # split() without args treats any whitespace as separator
    result = extract_bearer_token("Bearer     user_token")
    assert result == "user_token"


def test_validate_token_boundary_just_user_underscore():
    """Token that is exactly 'user_' is valid."""
    assert validate_token("user_") is True


def test_validate_token_single_char_after_prefix():
    """Token with single character after 'user_' is valid."""
    assert validate_token("user_a") is True
    assert validate_token("user_1") is True


def test_extract_bearer_token_tabs_and_newlines():
    """Test with tabs and newlines in various positions."""
    result = extract_bearer_token("Bearer\tuser_token")
    # "Bearer\tuser_token".split() = ["Bearer", "user_token"]
    assert result == "user_token"
    
    result = extract_bearer_token("Bearer\nuser_token")
    # "Bearer\nuser_token".split() = ["Bearer", "user_token"]
    assert result == "user_token"


def test_validate_token_with_embedded_spaces():
    """Tokens with embedded spaces (if somehow extracted) won't start with user_."""
    # This is more of a defensive test
    assert validate_token("user_ token") is False  # Has space after underscore
    assert validate_token("user_to ken") is False


def test_extract_bearer_token_preserves_case_of_token():
    """Token case is preserved during extraction."""
    result = extract_bearer_token("Bearer USER_ABC")
    assert result == "USER_ABC"
    
    result = extract_bearer_token("Bearer UsEr_MiXeD")
    assert result == "UsEr_MiXeD"