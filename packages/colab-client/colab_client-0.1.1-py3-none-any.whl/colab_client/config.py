from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CLIENT_ID = (
    "1014160490159-cvot3bea7tgkp72a4m29h20d9ddo6bne.apps.googleusercontent.com"
)
DEFAULT_CLIENT_SECRET = "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"

COLAB_API_URL = "https://colab.research.google.com"
COLAB_GAPI_URL = "https://colab.pa.googleapis.com"
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"

DEFAULT_SCOPES = (
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/colaboratory",
)

DEFAULT_REDIRECT_PORT = 8085
DEFAULT_HTTP_TIMEOUT = 30
DEFAULT_KERNEL_WAIT_TIMEOUT = 90
DEFAULT_EXECUTION_TIMEOUT = 60
DEFAULT_KEEP_ALIVE_INTERVAL = 60


@dataclass
class Config:
    client_id: str = field(
        default_factory=lambda: os.environ.get("COLAB_CLIENT_ID", DEFAULT_CLIENT_ID)
    )
    client_secret: str = field(
        default_factory=lambda: os.environ.get(
            "COLAB_CLIENT_SECRET", DEFAULT_CLIENT_SECRET
        )
    )
    token_path: Path = field(
        default_factory=lambda: Path(
            os.environ.get("COLAB_TOKEN_PATH", Path.home() / ".colab_token.json")
        )
    )
    scopes: tuple[str, ...] = DEFAULT_SCOPES
    redirect_port: int = DEFAULT_REDIRECT_PORT
    http_timeout: int = DEFAULT_HTTP_TIMEOUT
    kernel_wait_timeout: int = DEFAULT_KERNEL_WAIT_TIMEOUT
    execution_timeout: int = DEFAULT_EXECUTION_TIMEOUT
    keep_alive_interval: int = DEFAULT_KEEP_ALIVE_INTERVAL
    insecure_transport: bool = field(
        default_factory=lambda: os.environ.get("OAUTHLIB_INSECURE_TRANSPORT", "0")
        == "1"
    )

    def __post_init__(self) -> None:
        if isinstance(self.token_path, str):
            self.token_path = Path(self.token_path)
        if self.insecure_transport:
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    @property
    def redirect_uri(self) -> str:
        return f"http://localhost:{self.redirect_port}/"

    @property
    def oauth_client_config(self) -> dict:
        return {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": AUTH_URI,
                "token_uri": TOKEN_URI,
                "redirect_uris": ["http://localhost"],
            }
        }
