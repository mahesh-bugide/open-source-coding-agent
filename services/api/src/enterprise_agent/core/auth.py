from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from enterprise_agent.core.config import Settings, get_settings


@dataclass(slots=True)
class AuthContext:
    user_id: str


class AuthProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def authenticate(self, api_key: str | None) -> AuthContext:
        if not self._settings.require_api_key:
            return AuthContext(user_id="dev-user")

        if not api_key or api_key != self._settings.dev_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

        return AuthContext(user_id="dev-user")


def get_auth_provider(settings: Settings = Depends(get_settings)) -> AuthProvider:
    return AuthProvider(settings)


def require_auth(
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    provider: AuthProvider = Depends(get_auth_provider),
) -> AuthContext:
    return provider.authenticate(x_api_key)
