"""Kubernetes helpers for app pod discovery, log streaming, and manifest apply."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from localargo.logging import logger
from localargo.utils.cli import (
    ensure_kubectl_available,
    run_subprocess,
)
from localargo.utils.proc import run_json, run_stream


def _kubeconfig_args(kubeconfig: str | None) -> list[str]:
    if not kubeconfig:
        return []
    # Allow both file paths and directories (ignore directories gracefully)
    path = Path(kubeconfig)
    if path.exists() and path.is_file():
        return ["--kubeconfig", str(path)]
    return ["--kubeconfig", str(path)]


def apply_manifests(files: list[str], *, kubeconfig: str | None = None) -> None:
    """
    Apply one or more manifest files using kubectl apply -f.

    Args:
        files (list[str]): List of file paths (YAML files or directories). Each
            will be passed to kubectl via repeated -f flags.
        kubeconfig (str | None): Optional kubeconfig file path. When provided,
            it's passed to kubectl via --kubeconfig.

    """
    if not files:
        return
    kubectl_path = ensure_kubectl_available()
    args: list[str] = [kubectl_path, *(_kubeconfig_args(kubeconfig)), "apply"]
    for f in files:
        args.extend(["-f", f])
    logger.info("Applying manifests: %s", ", ".join(files))
    run_subprocess(args)


def ensure_namespace(namespace: str) -> None:
    """Create namespace if it does not exist."""
    kubectl_path = ensure_kubectl_available()
    args = [kubectl_path, "get", "ns", namespace, "-o", "name"]
    result = run_subprocess(args, check=False)
    if result.returncode != 0:
        run_subprocess([kubectl_path, "create", "ns", namespace])


def upsert_secret(namespace: str, secret_name: str, data: dict[str, str]) -> None:
    """
    Create or update a generic secret with provided key/value pairs.

    Values are passed from environment; empty values are allowed and result in empty strings.
    """
    ensure_namespace(namespace)
    kubectl_path = ensure_kubectl_available()
    # Try create
    base = [kubectl_path, "-n", namespace, "create", "secret", "generic", secret_name]
    for k, v in data.items():
        base.extend(["--from-literal", f"{k}={v}"])
    create_result = run_subprocess(base, check=False)
    if create_result.returncode == 0:
        return

    # Fallback to kubectl create secret generic --dry-run=client -o yaml | kubectl apply -f -
    dry = [
        kubectl_path,
        "-n",
        namespace,
        "create",
        "secret",
        "generic",
        secret_name,
        "--dry-run=client",
        "-o",
        "yaml",
    ]
    for k, v in data.items():
        dry.extend(["--from-literal", f"{k}={v}"])
    # Pipe into apply using captured output for safer resource handling
    dry_result = run_subprocess(dry, check=True)
    run_subprocess([kubectl_path, "apply", "-f", "-"], check=True, input=dry_result.stdout)


if TYPE_CHECKING:  # imported only for type checking
    from collections.abc import Iterator


def list_pods_for_app(app: str, namespace: str) -> list[str]:
    """List pods associated with an app using common label conventions."""
    kubectl_path = ensure_kubectl_available()
    obj = run_json([kubectl_path, "get", "pods", "-n", namespace, "-o", "json"])
    items = obj.get("items", []) if isinstance(obj, dict) else []
    pods: list[str] = []
    for item in items:
        matched = _extract_pod_name_if_matches(item, app)
        if matched:
            pods.append(matched)
    return pods


def _matches_app(labels: dict[str, Any], app: str) -> bool:
    values = [
        labels.get("app.kubernetes.io/instance"),
        labels.get("app.kubernetes.io/name"),
        labels.get("app"),
        labels.get("argo-app"),
    ]
    return any(isinstance(v, str) and v == app for v in values)


def _extract_pod_name_if_matches(item: Any, app: str) -> str | None:  # noqa: ANN401
    meta = item.get("metadata", {}) if isinstance(item, dict) else {}
    name = meta.get("name")
    labels = meta.get("labels", {}) or {}
    if isinstance(labels, dict) and _matches_app(labels, app) and isinstance(name, str):
        return name
    return None


def get_secret_data(namespace: str, secret_name: str, jsonpath: str) -> str:
    """Get data from a secret using jsonpath."""
    kubectl_path = ensure_kubectl_available()
    args = [
        kubectl_path,
        "-n",
        namespace,
        "get",
        "secret",
        secret_name,
        "-o",
        jsonpath,
    ]
    return run_subprocess(args).stdout.strip()


def stream_logs(
    pod: str,
    namespace: str,
    *,
    container: str | None = None,
    since: str | None = None,
    follow: bool = True,
) -> Iterator[str]:
    """Stream logs from a pod, yielding lines as strings."""
    kubectl_path = ensure_kubectl_available()
    args = [kubectl_path, "logs", pod, "-n", namespace]
    if container:
        args.extend(["-c", container])
    if since:
        args.extend(["--since", since])
    if follow:
        args.append("-f")
    return run_stream(args)
