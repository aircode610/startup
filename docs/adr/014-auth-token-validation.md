# ADR-014: Auth Token Validation

## Status
Accepted

## Context
We have repeatedly seen outages and security incidents caused by fragile token parsing
and inconsistent validation across endpoints.

## Decision
1. Auth tokens **must** be parsed defensively:
   - Missing or malformed `Authorization` headers must **not** raise exceptions.
   - Prefer a single shared helper for parsing: `extract_bearer_token(...)`.

2. Token validation is centralized:
   - All tokens are validated via `validate_token(...)`.
   - Any endpoint/business logic must treat empty/None tokens as invalid.

3. Logging rules:
   - **Never** log raw tokens (even at debug level).
   - If needed, log only "token present" boolean.

## Consequences
- Changes to auth logic are **high-risk** and require targeted unit tests:
  - empty header
  - wrong scheme
  - malformed header
  - valid/invalid tokens

