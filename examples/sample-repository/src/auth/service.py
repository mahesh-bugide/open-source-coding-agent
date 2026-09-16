DEFAULT_TIMEOUT_SECONDS = 0


def issue_session_token(user_id: str, timeout_seconds: int = 0) -> tuple[str, int]:
    if not user_id:
        raise ValueError("user_id is required")

    token = f"token-{user_id}"
    # BUG: ignores timeout_seconds and always sets ttl to zero.
    return token, 0
