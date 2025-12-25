"""Test configuration and global fixtures for localargo tests."""

# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, Mock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path

# =============================================================================
# Mock CLI tool paths - used throughout the test suite for consistent mocking
# =============================================================================
MOCK_CLI_PATHS = {
    "kind": "/usr/local/bin/kind",
    "k3s": "/usr/local/bin/k3s",
    "kubectl": "/usr/local/bin/kubectl",
    "helm": "/usr/local/bin/helm",
    "argocd": "/usr/local/bin/argocd",
}


def get_cli_name(cmd: list[str]) -> str | None:
    """Extract CLI tool name from command, handling both bare names and full paths."""
    if not cmd:
        return None
    first_arg = str(cmd[0])
    # Check if it's a full path matching our mocked paths
    for name, path in MOCK_CLI_PATHS.items():
        if first_arg in (path, name):
            return name
    return None


# =============================================================================
# Subprocess mock handler - routes commands to appropriate mock handlers
# =============================================================================


class SubprocessMockHandler:
    """Centralized handler for subprocess.run mock responses."""

    @staticmethod
    def handle(cmd: list[str]) -> MagicMock:
        """Route command to appropriate handler and return mock result."""
        result = MagicMock()
        result.returncode = 0
        result.stdout = ""
        result.stderr = ""

        if not cmd:
            return result

        cli_name = get_cli_name(cmd)
        if cli_name == "kind":
            SubprocessMockHandler._handle_kind(cmd, result)
        elif cli_name == "k3s":
            SubprocessMockHandler._handle_k3s(cmd, result)
        elif cli_name == "kubectl":
            SubprocessMockHandler._handle_kubectl(cmd, result)
        elif cli_name == "helm":
            SubprocessMockHandler._handle_helm(cmd, result)
        elif cli_name == "argocd":
            SubprocessMockHandler._handle_argocd(cmd, result)

        return result

    @staticmethod
    def _handle_kind(cmd: list[str], result: MagicMock) -> None:
        """Handle kind commands."""
        if "version" in cmd:
            result.stdout = "kind v0.20.0 go1.20.0"
        elif "get" in cmd and "clusters" in cmd:
            result.stdout = "demo\nother-cluster\n"

    @staticmethod
    def _handle_k3s(cmd: list[str], result: MagicMock) -> None:
        """Handle k3s commands."""
        if len(cmd) > 1 and cmd[1] == "--version":
            result.stdout = "k3s version v1.27.0+k3s1"

    @staticmethod
    def _handle_kubectl(cmd: list[str], result: MagicMock) -> None:
        """Handle kubectl commands."""
        # Convert to string for easier matching
        cmd_str = " ".join(cmd)

        if "cluster-info" in cmd:
            result.stdout = "Kubernetes control plane is running"
            return

        # Handle kubectl get secret commands
        if "get" in cmd and "secret" in cmd:
            SubprocessMockHandler._handle_kubectl_secret(cmd, result)
            return

        # Handle kubectl get deployment commands
        if "get" in cmd and "deployment" in cmd:
            SubprocessMockHandler._handle_kubectl_deployment(cmd, cmd_str, result)
            return

        # Return a small pod list for get pods -o json
        if "get" in cmd and "pods" in cmd and "-o" in cmd and "json" in cmd:
            result.stdout = json.dumps(
                {
                    "items": [
                        {"metadata": {"name": "app-0", "labels": {"app": "myapp"}}},
                        {"metadata": {"name": "app-1", "labels": {"app.kubernetes.io/name": "myapp"}}},
                        {"metadata": {"name": "other", "labels": {"app": "other"}}},
                    ]
                }
            )
            return

        # Handle kubectl get ingress commands
        if "get" in cmd and "ingress" in cmd and "argocd-server" in cmd:
            result.stdout = "argocd.localtest.me"
            return

        # Handle other kubectl commands (patch, delete, create, wait) - succeed silently
        if any(action in cmd for action in ["patch", "delete", "create", "wait"]):
            result.stdout = ""

    @staticmethod
    def _handle_kubectl_secret(cmd: list[str], result: MagicMock) -> None:
        """Handle kubectl get secret commands."""
        secret_name = None
        for i, arg in enumerate(cmd):
            if arg == "secret" and i + 1 < len(cmd):
                secret_name = cmd[i + 1]
                break

        if secret_name == "argocd-initial-admin-secret":
            # Return base64-encoded "admin" as the default password
            result.stdout = base64.b64encode(b"admin").decode("utf-8")
        elif secret_name == "localargo-root-ca":
            # Return base64-encoded dummy certificate data
            dummy_cert = (
                b"-----BEGIN CERTIFICATE-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA\n-----END CERTIFICATE-----"
            )
            result.stdout = base64.b64encode(dummy_cert).decode("utf-8")
        elif secret_name:
            result.stdout = secret_name

    @staticmethod
    def _handle_kubectl_deployment(cmd: list[str], cmd_str: str, result: MagicMock) -> None:
        """Handle kubectl get deployment commands."""
        # Check if this is a jsonpath query for ready replicas
        is_jsonpath_query = "jsonpath" in cmd_str

        if "argocd-server" in cmd:
            if is_jsonpath_query and "readyReplicas" in cmd_str:
                result.stdout = "1"
            elif is_jsonpath_query and "Available" in cmd_str:
                result.stdout = "True"
            else:
                result.stdout = "argocd-server"
        elif "ingress-nginx-controller" in cmd:
            if is_jsonpath_query and "readyReplicas" in cmd_str:
                result.stdout = "2"
            elif is_jsonpath_query and "Available" in cmd_str:
                result.stdout = "True"
            else:
                result.stdout = "ingress-nginx-controller"
        elif "cert-manager" in cmd:
            if is_jsonpath_query and "Available" in cmd_str:
                result.stdout = "True"
            else:
                result.stdout = "cert-manager"

    @staticmethod
    def _handle_helm(cmd: list[str], result: MagicMock) -> None:
        """Handle helm commands."""
        if "repo" in cmd and "add" in cmd:
            result.stdout = ""
        elif "repo" in cmd and "update" in cmd:
            result.stdout = "Hang tight while we grab the latest from your chart repositories..."

    @staticmethod
    def _handle_argocd(cmd: list[str], result: MagicMock) -> None:
        """Handle argocd commands."""
        if "account" in cmd and "get-user-info" in cmd:
            result.stdout = "{}"
        elif len(cmd) > 1 and cmd[1] == "logout":
            result.stdout = "Logged out"
        elif len(cmd) > 1 and cmd[1] == "login":
            result.stdout = "Login Succeeded"
        elif SubprocessMockHandler._is_argocd_app_list(cmd):
            result.stdout = json.dumps(
                [
                    {
                        "metadata": {"name": "myapp"},
                        "spec": {"destination": {"namespace": "default"}},
                        "status": {
                            "health": {"status": "Healthy"},
                            "sync": {"status": "Synced", "revision": "abcd1234"},
                        },
                    }
                ]
            )
        elif SubprocessMockHandler._is_argocd_app_get(cmd):
            app_name = cmd[3] if len(cmd) > 3 else "myapp"  # noqa: PLR2004
            result.stdout = json.dumps(
                {
                    "metadata": {"name": app_name},
                    "spec": {"destination": {"namespace": "default"}},
                    "status": {
                        "health": {"status": "Healthy"},
                        "sync": {"status": "Synced", "revision": "abcd1234"},
                    },
                }
            )
        else:
            result.stdout = ""

    @staticmethod
    def _is_argocd_app_list(cmd: list[str]) -> bool:
        """Check if command is argocd app list -o json."""
        return (
            len(cmd) >= 4  # noqa: PLR2004
            and "app" in cmd
            and "list" in cmd
            and "-o" in cmd
            and "json" in cmd
        )

    @staticmethod
    def _is_argocd_app_get(cmd: list[str]) -> bool:
        """Check if command is argocd app get -o json."""
        return (
            len(cmd) >= 5  # noqa: PLR2004
            and "app" in cmd
            and "get" in cmd
            and "-o" in cmd
            and "json" in cmd
        )


# =============================================================================
# Auto-use fixtures - applied to all tests
# =============================================================================


@pytest.fixture(autouse=True)
def mock_subprocess_run() -> Generator[MagicMock, None, None]:
    """Patch subprocess.run globally to prevent actual shell commands."""

    def mock_run_side_effect(*args: Any, **_kwargs: Any) -> MagicMock:  # noqa: ANN401
        cmd = args[0] if args else []
        if not isinstance(cmd, list):
            cmd = []
        return SubprocessMockHandler.handle(cmd)

    with patch("subprocess.run", side_effect=mock_run_side_effect) as mock_run:
        yield mock_run


@pytest.fixture(autouse=True)
def mock_subprocess_popen() -> Generator[MagicMock, None, None]:
    """Patch subprocess.Popen for background processes."""
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.returncode = 0
        mock_process.pid = 12345
        mock_process.stdout = iter(())  # Empty iterator for streaming
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process
        yield mock_popen


@pytest.fixture(autouse=True)
def mock_shutil_which() -> Generator[MagicMock, None, None]:
    """Patch shutil.which to simulate available tools."""

    def mock_which(cmd: str) -> str | None:
        return MOCK_CLI_PATHS.get(cmd)

    with patch("shutil.which", side_effect=mock_which) as mock_which_func:
        yield mock_which_func


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent accidental real sleeps during tests."""
    monkeypatch.setattr("time.sleep", lambda *_: None)


# =============================================================================
# Shared test utilities and fixtures
# =============================================================================


@pytest.fixture
def sample_cluster_yaml() -> str:
    """Return common YAML content for a single test cluster."""
    return """
clusters:
  - name: test-cluster
    provider: kind
"""


@pytest.fixture
def sample_multi_cluster_yaml() -> str:
    """Return common YAML content for multiple test clusters."""
    return """
clusters:
  - name: cluster1
    provider: kind
  - name: cluster2
    provider: k3s
"""


@pytest.fixture
def create_manifest_file(tmp_path: Path) -> Callable[[str | None, str], Path]:
    """Create a temporary manifest file factory."""
    default_content = """
clusters:
  - name: test-cluster
    provider: kind
"""

    def _create_file(yaml_content: str | None = None, filename: str = "clusters.yaml") -> Path:
        content = yaml_content if yaml_content is not None else default_content
        manifest_file = tmp_path / filename
        manifest_file.write_text(content)
        return manifest_file

    return _create_file


@pytest.fixture
def create_mock_provider() -> Callable[..., Mock]:
    """Create a mock provider factory."""

    def _create_mock(name: str = "test-cluster", **kwargs: Any) -> Mock:  # noqa: ANN401
        mock_provider = Mock()
        mock_provider.name = name
        mock_provider.provider_name = kwargs.get("provider_name", "kind")
        mock_provider.is_available.return_value = True
        mock_provider.get_cluster_status.return_value = {
            "exists": True,
            "ready": True,
            "context": f"kind-{name}",
            "provider": "kind",
            "name": name,
        }
        for key, value in kwargs.items():
            setattr(mock_provider, key, value)
        return mock_provider

    return _create_mock


# =============================================================================
# Helper functions for test assertions
# =============================================================================


def assert_command_contains(call_args: Any, expected_parts: list[str]) -> None:  # noqa: ANN401
    """Assert that a subprocess call contains expected command parts (ignoring path prefixes)."""
    cmd = call_args[0][0] if call_args[0] else call_args.args[0]
    # Normalize: extract just the command names without paths
    cmd_parts = [str(c).split("/")[-1] if "/" in str(c) else str(c) for c in cmd]
    for part in expected_parts:
        assert part in cmd_parts, f"Expected '{part}' in command {cmd_parts}"


def assert_command_starts_with(call_args: Any, expected_cmd: str) -> None:  # noqa: ANN401
    """Assert that a subprocess call starts with the expected command (ignoring path)."""
    cmd = call_args[0][0] if call_args[0] else call_args.args[0]
    first_arg = str(cmd[0])
    # Extract just the command name without path
    cmd_name = first_arg.split("/")[-1] if "/" in first_arg else first_arg
    assert cmd_name == expected_cmd, f"Expected command '{expected_cmd}' but got '{cmd_name}'"
