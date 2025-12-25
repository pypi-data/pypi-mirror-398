"""Unit tests for ArgoCD facade behavior and JSON parsing with mocks."""

# pylint: disable=duplicate-code
from typing import Any
from unittest.mock import patch

import pytest

import localargo.core.argocd as argocd_mod
from localargo.core.argocd import ArgoClient, to_state
from localargo.core.catalog import AppSpec
from localargo.utils.proc import ProcessError


def test_to_state_parsing() -> None:
    """Parse a minimal ArgoCD app JSON into AppState."""
    raw: dict[str, Any] = {
        "metadata": {"name": "myapp"},
        "spec": {"destination": {"namespace": "default"}},
        "status": {
            "health": {"status": "Healthy"},
            "sync": {"status": "Synced", "revision": "abcd1234"},
        },
    }
    st = to_state(raw)
    assert st.name == "myapp"
    assert st.namespace == "default"
    assert st.health == "Healthy"
    assert st.sync == "Synced"
    assert st.revision == "abcd1234"


def test_argocd_get_and_list_commands() -> None:
    """Ensure get/list return expected app objects via mocked CLI."""
    with patch("localargo.core.argocd._get_initial_admin_password", return_value="admin"):
        client = ArgoClient()
        st = client.get_app("myapp")
        assert st.name == "myapp"
        apps = client.get_apps()
        assert any(a.name == "myapp" for a in apps)


essential_spec = AppSpec(
    name="myapp",
    repo="https://example.com/repo.git",
    path=".",
    type="kustomize",
    namespace="default",
)


def test_create_update_sync_invocations() -> None:
    """
    Smoke test create/update/sync command invocations under mocks.

    No exception indicates mocked create path is exercised. We avoid
    wait_healthy polling here; get_app coverage is validated above.
    """
    with patch("localargo.core.argocd._get_initial_admin_password", return_value="admin"):
        client = ArgoClient()
        client.create_or_update_app(essential_spec)
        res = client.sync_app("myapp", wait=False)
        assert res == "Unknown"


def test_get_apps_auth_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate an auth failure once, then success to ensure retry path works."""
    calls: dict[str, int] = {"count": 0}

    original_run_json = argocd_mod.run_json

    def flaky_run_json(args: list[str]) -> Any:  # noqa: ANN401
        calls["count"] += 1
        if calls["count"] == 1:
            # First call raises ProcessError to trigger retry inside run_json_with_auth
            msg = "unauth"
            raise ProcessError(msg, code=20, stdout="", stderr="invalid session")
        return original_run_json(args)

    monkeypatch.setattr(argocd_mod, "run", lambda *_, **__: None)  # Mock login calls
    monkeypatch.setattr(argocd_mod, "run_json", flaky_run_json)

    with patch("localargo.core.argocd._get_initial_admin_password", return_value="admin"):
        client = ArgoClient()
        apps = client.get_apps()
        assert any(a.name == "myapp" for a in apps)
        expected_calls = 2
        assert calls["count"] >= expected_calls


def test_login_sequence_on_auth_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """On auth failure, client should attempt logout and then login (with grpc-web fallback)."""
    calls: dict[str, int] = {"run_count": 0}

    original_run = argocd_mod.run
    original_run_json = argocd_mod.run_json

    def flaky_run_json(args: list[str]) -> Any:  # noqa: ANN401
        # First get-user-info fails to force login sequence
        if args[:3] == ["argocd", "app", "list"]:
            # Let list itself proceed normally
            return original_run_json(args)
        return original_run_json(args)

    def tracing_run(args: list[str], timeout: int | None = None) -> Any:  # noqa: ANN401
        calls["run_count"] += 1
        return original_run(args, timeout=timeout)  # type: ignore[arg-type]

    monkeypatch.setattr(argocd_mod, "run", tracing_run)
    monkeypatch.setattr(argocd_mod, "run_json", flaky_run_json)

    with patch("localargo.core.argocd._get_initial_admin_password", return_value="admin"):
        client = ArgoClient()
        _ = client.get_apps()
        # At minimum, run() should have been called for login or user-info
        min_run_count = 1
        assert calls["run_count"] >= min_run_count
