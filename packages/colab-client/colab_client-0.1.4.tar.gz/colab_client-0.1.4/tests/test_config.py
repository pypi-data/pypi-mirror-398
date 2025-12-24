from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from colab_client.config import (
    AUTH_URI,
    DEFAULT_CLIENT_ID,
    DEFAULT_CLIENT_SECRET,
    DEFAULT_EXECUTION_TIMEOUT,
    DEFAULT_HTTP_TIMEOUT,
    DEFAULT_KEEP_ALIVE_INTERVAL,
    DEFAULT_KERNEL_WAIT_TIMEOUT,
    DEFAULT_REDIRECT_PORT,
    DEFAULT_SCOPES,
    TOKEN_URI,
    Config,
)


class TestConfigDefaults:
    def test_default_values(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.client_id == DEFAULT_CLIENT_ID
            assert config.client_secret == DEFAULT_CLIENT_SECRET
            assert config.scopes == DEFAULT_SCOPES
            assert config.redirect_port == DEFAULT_REDIRECT_PORT
            assert config.http_timeout == DEFAULT_HTTP_TIMEOUT
            assert config.kernel_wait_timeout == DEFAULT_KERNEL_WAIT_TIMEOUT
            assert config.execution_timeout == DEFAULT_EXECUTION_TIMEOUT
            assert config.keep_alive_interval == DEFAULT_KEEP_ALIVE_INTERVAL
            assert config.insecure_transport is False

    def test_token_path_default(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.token_path == Path.home() / ".colab_token.json"


class TestConfigEnvVars:
    def test_client_id_from_env(self) -> None:
        with mock.patch.dict(os.environ, {"COLAB_CLIENT_ID": "custom-id"}):
            config = Config()
            assert config.client_id == "custom-id"

    def test_client_secret_from_env(self) -> None:
        with mock.patch.dict(os.environ, {"COLAB_CLIENT_SECRET": "custom-secret"}):
            config = Config()
            assert config.client_secret == "custom-secret"

    def test_token_path_from_env(self) -> None:
        with mock.patch.dict(os.environ, {"COLAB_TOKEN_PATH": "/custom/path/token.json"}):
            config = Config()
            assert config.token_path == Path("/custom/path/token.json")

    def test_insecure_transport_enabled(self) -> None:
        with mock.patch.dict(os.environ, {"OAUTHLIB_INSECURE_TRANSPORT": "1"}):
            config = Config()
            assert config.insecure_transport is True
            assert os.environ.get("OAUTHLIB_INSECURE_TRANSPORT") == "1"


class TestConfigProperties:
    def test_redirect_uri(self) -> None:
        config = Config(redirect_port=9000)
        assert config.redirect_uri == "http://localhost:9000/"

    def test_oauth_client_config(self) -> None:
        config = Config(client_id="test-id", client_secret="test-secret")
        oauth_config = config.oauth_client_config
        assert oauth_config["installed"]["client_id"] == "test-id"
        assert oauth_config["installed"]["client_secret"] == "test-secret"
        assert oauth_config["installed"]["auth_uri"] == AUTH_URI
        assert oauth_config["installed"]["token_uri"] == TOKEN_URI
        assert "http://localhost" in oauth_config["installed"]["redirect_uris"]


class TestConfigPostInit:
    def test_token_path_string_converted_to_path(self) -> None:
        config = Config(token_path="/some/path/token.json")  # type: ignore[arg-type]
        assert isinstance(config.token_path, Path)
        assert config.token_path == Path("/some/path/token.json")
