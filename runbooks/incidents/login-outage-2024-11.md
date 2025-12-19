# Incident: Login Outage (Nov 2024)

## Summary
A refactor to token parsing caused unhandled exceptions on malformed `Authorization` headers,
leading to a partial outage of authenticated flows.

## Impact
- ~28 minutes degraded service for authenticated checkout.
- Elevated error rate and increased on-call load.

## Root Cause
Auth parsing assumed header shape `"Bearer <token>"` and accessed missing parts,
raising exceptions for:
- empty headers
- headers with extra spaces
- non-bearer schemes

## Corrective Actions / Precedent
- Token parsing must be defensive and never raise.
- Add unit tests covering malformed headers.
- Treat empty/None tokens as invalid.
- Avoid logging raw tokens.

