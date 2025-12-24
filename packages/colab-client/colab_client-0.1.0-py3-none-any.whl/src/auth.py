from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .config import TOKEN_URI, Config
from .exceptions import AuthenticationError, TokenRefreshError

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class Authenticator:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._credentials: Credentials | None = None

    @property
    def credentials(self) -> Credentials | None:
        return self._credentials

    @property
    def token(self) -> str:
        if not self._credentials:
            raise AuthenticationError("Not authenticated")
        return self._credentials.token or ""

    @property
    def is_authenticated(self) -> bool:
        return self._credentials is not None

    def login(self, interactive: bool = True) -> bool:
        if self._load_cached_token():
            return True

        if not interactive:
            raise AuthenticationError(
                "No valid cached credentials and interactive login disabled"
            )

        return self._perform_oauth_flow()

    def _load_cached_token(self) -> bool:
        token_path = self._config.token_path
        if not token_path.exists():
            return False

        try:
            token_data = json.loads(token_path.read_text())
            self._credentials = Credentials(
                token=token_data.get("token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri=TOKEN_URI,
                client_id=self._config.client_id,
                client_secret=self._config.client_secret,
                scopes=list(self._config.scopes),
            )

            if self._credentials.expired and self._credentials.refresh_token:
                self._refresh_token()

            logger.info("Loaded existing credentials")
            return True

        except Exception as e:
            logger.warning("Failed to load cached credentials: %s", e)
            return False

    def _perform_oauth_flow(self) -> bool:
        flow = InstalledAppFlow.from_client_config(
            self._config.oauth_client_config,
            scopes=list(self._config.scopes),
            redirect_uri=self._config.redirect_uri,
        )

        auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")

        print("\n" + "=" * 60)
        print("Open the following URL in your browser to login:\n")
        print(auth_url)
        print("\n" + "=" * 60)
        print("\nAfter login, you will be redirected to localhost.")
        print("Copy the ENTIRE URL from the address bar (including ?code=...)")
        print("and paste it here:\n")

        redirect_response = input("> ").strip()
        flow.fetch_token(authorization_response=redirect_response)

        self._credentials = flow.credentials
        self._save_token()

        logger.info("Login successful")
        return True

    def refresh(self) -> bool:
        if not self._credentials or not self._credentials.refresh_token:
            return False

        try:
            self._refresh_token()
            return True
        except TokenRefreshError:
            return False

    def _refresh_token(self) -> None:
        if not self._credentials:
            raise TokenRefreshError("No credentials to refresh")

        try:
            self._credentials.refresh(Request())
            self._save_token()
            logger.info("Token refreshed")
        except Exception as e:
            raise TokenRefreshError(f"Failed to refresh token: {e}") from e

    def _save_token(self) -> None:
        if not self._credentials:
            return

        token_data = {
            "token": self._credentials.token,
            "refresh_token": self._credentials.refresh_token,
        }
        self._config.token_path.write_text(json.dumps(token_data))

    def clear_token(self) -> None:
        if self._config.token_path.exists():
            self._config.token_path.unlink()
        self._credentials = None
