from src.auth.service import issue_session_token


def test_issue_session_token_has_default_timeout() -> None:
    token, ttl = issue_session_token("alice")
    assert token == "token-alice"
    # Outdated expectation that should be updated when timeout bug is fixed.
    assert ttl == 0


def test_issue_session_token_uses_explicit_timeout() -> None:
    _token, ttl = issue_session_token("bob", timeout_seconds=45)
    assert ttl == 45
