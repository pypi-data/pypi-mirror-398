# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
"""CA management commands."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from localargo.logging import logger
from localargo.utils.cli import (
    ensure_kubectl_available,
    run_subprocess,
)

# =============================================================================
# Component configuration for CA status checks
# =============================================================================


@dataclass(frozen=True)
class CAComponentCheck:
    """Configuration for a CA component status check."""

    key: str
    display_name: str
    description: str
    ready_text: str  # e.g., "Ready" or "Exists"


# Define all CA components to check
CA_COMPONENTS = [
    CAComponentCheck("cert_manager", "cert-manager", "Certificate management controller", "Ready"),
    CAComponentCheck("trust_manager", "trust-manager", "Trust bundle distribution", "Ready"),
    CAComponentCheck("root_ca", "Root CA", "Self-signed root certificate", "Ready"),
    CAComponentCheck("cluster_issuer", "Cluster Issuer", "Certificate issuer configuration", "Exists"),
    CAComponentCheck("wildcard_cert", "Wildcard Certificate", "*.localtest.me certificate", "Ready"),
    CAComponentCheck("trust_bundle", "Trust Bundle", "CA distribution to all namespaces", "Exists"),
    CAComponentCheck("user_secret", "User CA Secret", "Secret localargo-ca-cert in namespace ingress-nginx", "Exists"),
]


# =============================================================================
# CLI command
# =============================================================================


@click.group(name="ca")
def ca_group() -> None:
    """Manage Certificate Authority setup."""


@ca_group.command(name="status")
@click.pass_context
def ca_status_cmd(_ctx: click.Context) -> None:
    """Show status of CA components."""
    console = Console()

    try:
        status = _get_ca_status()
        _display_ca_status(console, status)

    except Exception as e:
        logger.error("Failed to get CA status: %s", e)
        raise click.ClickException(str(e)) from e


# =============================================================================
# Status collection - individual check functions
# =============================================================================


def _check_deployment_available(kubectl_path: str, name: str, namespace: str) -> bool:
    """Check if a deployment is available."""
    try:
        result = run_subprocess(
            [
                kubectl_path,
                "get",
                "deployment",
                name,
                "-n",
                namespace,
                "-o",
                "jsonpath={.status.conditions[?(@.type=='Available')].status}",
            ],
            check=True,
        )
        return result.stdout.strip() == "True"
    except (subprocess.CalledProcessError, OSError):
        return False


def _check_certificate_ready(kubectl_path: str, name: str, namespace: str) -> bool:
    """Check if a certificate is ready."""
    try:
        result = run_subprocess(
            [
                kubectl_path,
                "get",
                "certificate",
                name,
                "-n",
                namespace,
                "-o",
                "jsonpath={.status.conditions[?(@.type=='Ready')].status}",
            ],
            check=True,
        )
        return result.stdout.strip() == "True"
    except (subprocess.CalledProcessError, OSError):
        return False


def _check_resource_exists(kubectl_path: str, resource_type: str, name: str, namespace: str | None = None) -> bool:
    """Check if a Kubernetes resource exists."""
    try:
        cmd = [kubectl_path, "get", resource_type, name]
        if namespace:
            cmd.extend(["-n", namespace])
        run_subprocess(cmd, check=True)
    except (subprocess.CalledProcessError, OSError):
        return False
    else:
        return True


# =============================================================================
# Main status collection
# =============================================================================


def _get_ca_status() -> dict[str, Any]:
    """Get comprehensive CA status."""
    kubectl_path = ensure_kubectl_available()

    return {
        "cert_manager": _check_deployment_available(kubectl_path, "cert-manager", "cert-manager"),
        "trust_manager": _check_deployment_available(kubectl_path, "trust-manager", "cert-manager"),
        "root_ca": _check_certificate_ready(kubectl_path, "localargo-root-ca", "cert-manager"),
        "cluster_issuer": _check_resource_exists(kubectl_path, "clusterissuer", "localargo-dev-ca"),
        "wildcard_cert": _check_certificate_ready(kubectl_path, "localargo-wildcard-cert", "ingress-nginx"),
        "trust_bundle": _check_resource_exists(kubectl_path, "bundle", "localargo-ca-bundle", "cert-manager"),
        "user_secret": _check_resource_exists(kubectl_path, "secret", "localargo-ca-cert", "ingress-nginx"),
    }


# =============================================================================
# Status display
# =============================================================================


def _format_status_text(is_ready: bool, ready_text: str) -> str:
    """Format status text with emoji based on readiness."""
    if is_ready:
        return f"✅ {ready_text}"
    return f"❌ Not {ready_text}" if ready_text == "Ready" else "❌ Missing"


def _display_ca_status(console: Console, status: dict[str, Any]) -> None:
    """Display CA status in a table."""
    table = Table(title="Certificate Authority Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    for component in CA_COMPONENTS:
        is_ready = status.get(component.key, False)
        status_text = _format_status_text(is_ready, component.ready_text)
        table.add_row(component.display_name, status_text, component.description)

    console.print(table)
    _display_summary(console, status)


def _display_summary(console: Console, status: dict[str, Any]) -> None:
    """Display CA setup summary."""
    all_ready = all(status.values())
    if all_ready:
        console.print("\n[green]🎉 CA setup is complete![/green]")
        console.print("All workloads can now trust certificates signed by the localargo CA.")
    else:
        console.print("\n[yellow]⚠️  CA setup is incomplete.[/yellow]")
        console.print("Run 'localargo up' to complete the setup.")
