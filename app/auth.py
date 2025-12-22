from __future__ import annotations


def extract_bearer_token(authorization_header: str | None) -> str | None:
    """
    Extracts the token from: "Bearer <token>"

    Defensive by design:
    - Returns None if header is missing/malformed
    - Never raises
    """
    if not authorization_header:
        return None

    parts = authorization_header.split()
    if len(parts) != 2:
        return None

    scheme, token = parts[0], parts[1]
    if scheme.lower() != "bearer":
        return None

    token = token.strip()
    if not token:
        return None

    return token


def validate_token(token: str | None) -> bool:
    """
    Marketplace demo auth rule:
    - Valid tokens start with "user_"
    - Empty/malformed tokens are invalid
    """
    if not token:
        return False
    return token.startswith("user_")

