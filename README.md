# Precedent Demo Marketplace

A tiny marketplace-style backend repo built to demo:
- **precedent-aware PR review** (ADRs + incidents)
- **AI-generated unit tests** (via CodeRabbit)
- **executed evidence** in a clean environment (Daytona)

## Quickstart

Create a venv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run tests:

```bash
pytest -q
```

Run API:

```bash
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Demo PR script

Make a PR that changes `app/auth.py` (e.g., refactor parsing/validation).

In the PR, comment:

```
@coderabbitai generate unit tests
```

CodeRabbit will add missing tests for auth edge cases.

Your evidence runner will execute the tests in a clean environment and post results.

## Precedents in this repo

- **ADR**: `docs/adr/014-auth-token-validation.md`
- **Incident**: `runbooks/incidents/login-outage-2024-11.md`

---

## Suggested "Demo PR" change (for your storyline)

Edit `app/auth.py` and (intentionally) introduce a bug to show the value of generated tests:

Change:

```python
def validate_token(token: str | None) -> bool:
    if not token:
        return False
    return token.startswith("user_")
```

to the buggy version:

```python
def validate_token(token: str | None) -> bool:
    return token.startswith("user_")  # bug: token can be None
```

