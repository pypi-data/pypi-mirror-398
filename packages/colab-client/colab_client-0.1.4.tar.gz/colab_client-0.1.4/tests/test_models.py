from __future__ import annotations

import pytest

from colab_client.models import (
    AcceleratorType,
    Assignment,
    ExecutionError,
    ExecutionResult,
    KernelState,
    ProxyInfo,
    RuntimeVariant,
    Session,
)


class TestAcceleratorType:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("", AcceleratorType.NONE),
            ("NONE", AcceleratorType.NONE),
            ("none", AcceleratorType.NONE),
            ("GPU", AcceleratorType.GPU),
            ("TPU", AcceleratorType.TPU),
            ("invalid", AcceleratorType.NONE),
        ],
    )
    def test_from_string(self, value: str, expected: AcceleratorType) -> None:
        assert AcceleratorType.from_string(value) == expected


class TestRuntimeVariant:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("", RuntimeVariant.DEFAULT),
            ("DEFAULT", RuntimeVariant.DEFAULT),
            ("STANDARD_GPU", RuntimeVariant.STANDARD_GPU),
            ("PREMIUM_GPU", RuntimeVariant.PREMIUM_GPU),
            ("TPU", RuntimeVariant.TPU),
            ("CASCADE_LAKE", RuntimeVariant.CASCADE_LAKE),
            ("SKYLAKE", RuntimeVariant.SKYLAKE),
            ("invalid", RuntimeVariant.DEFAULT),
        ],
    )
    def test_from_string(self, value: str, expected: RuntimeVariant) -> None:
        assert RuntimeVariant.from_string(value) == expected


class TestProxyInfo:
    def test_frozen(self) -> None:
        proxy = ProxyInfo(url="https://example.com", token="abc123")
        with pytest.raises(AttributeError):
            proxy.url = "https://other.com"  # type: ignore[misc]


class TestAssignment:
    def test_proxy_url_with_proxy_info(self) -> None:
        proxy = ProxyInfo(url="https://proxy.example.com", token="token123")
        assignment = Assignment(endpoint="test-endpoint", proxy_info=proxy)
        assert assignment.proxy_url == "https://proxy.example.com"
        assert assignment.proxy_token == "token123"

    def test_proxy_url_without_proxy_info(self) -> None:
        assignment = Assignment(endpoint="test-endpoint")
        assert assignment.proxy_url == ""
        assert assignment.proxy_token == ""

    def test_defaults(self) -> None:
        assignment = Assignment(endpoint="test")
        assert assignment.accelerator == AcceleratorType.NONE
        assert assignment.variant == RuntimeVariant.DEFAULT
        assert assignment.proxy_info is None


class TestSession:
    def test_defaults(self) -> None:
        session = Session(id="sess-1", kernel_id="kern-1", path="/notebook.ipynb")
        assert session.state == KernelState.UNKNOWN


class TestExecutionResult:
    def test_success_without_error(self) -> None:
        result = ExecutionResult(stdout="output")
        assert result.success is True

    def test_success_with_error(self) -> None:
        error = ExecutionError(name="ValueError", value="invalid")
        result = ExecutionResult(error=error)
        assert result.success is False

    def test_defaults(self) -> None:
        result = ExecutionResult()
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.result is None
        assert result.error is None
        assert result.display_data == []


class TestExecutionError:
    def test_str(self) -> None:
        error = ExecutionError(name="TypeError", value="expected str, got int")
        assert str(error) == "TypeError: expected str, got int"

    def test_defaults(self) -> None:
        error = ExecutionError(name="Error", value="msg")
        assert error.traceback == []
