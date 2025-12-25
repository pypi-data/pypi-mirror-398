# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
"""
CoreDNS configuration for localargo.

This module provides functionality to configure CoreDNS to rewrite
*.localtest.me (and other configured domains) queries to the ingress-nginx
service, enabling in-cluster resolution of ingress hostnames.

This solves the problem where pods inside the cluster cannot resolve
*.localtest.me hostnames because they resolve to 127.0.0.1 externally,
which is unreachable from inside the cluster.
"""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

from localargo.logging import logger
from localargo.utils.cli import ensure_kubectl_available, run_subprocess

if TYPE_CHECKING:
    from localargo.config.manifest import CoreDnsRewriteConfig

# =============================================================================
# Constants
# =============================================================================

COREDNS_CONFIGMAP_NAME = "coredns"
COREDNS_NAMESPACE = "kube-system"
INGRESS_SERVICE_FQDN = "ingress-nginx-controller.ingress-nginx.svc.cluster.local"

# Marker comment to identify localargo-managed rewrite rules
LOCALARGO_MARKER_START = "# BEGIN localargo coredns rewrite"
LOCALARGO_MARKER_END = "# END localargo coredns rewrite"


# =============================================================================
# CoreDNS Configuration
# =============================================================================


def configure_coredns_rewrite(config: CoreDnsRewriteConfig, ingress_namespace: str) -> None:
    """
    Configure CoreDNS to rewrite domain queries to the ingress service.

    This adds rewrite rules to the CoreDNS ConfigMap so that queries for
    *.localtest.me (and other configured domains) are resolved to the
    ingress-nginx-controller service instead of 127.0.0.1.

    Args:
        config (CoreDnsRewriteConfig): CoreDNS rewrite configuration containing domains to rewrite
        ingress_namespace (str): Namespace where ingress-nginx is installed

    """
    if not config.enabled:
        logger.info("CoreDNS rewrite is disabled, skipping configuration")
        return

    if not config.domains:
        logger.info("No domains configured for CoreDNS rewrite, skipping")
        return

    logger.info("Configuring CoreDNS to rewrite domains: %s", ", ".join(config.domains))

    # Get current CoreDNS ConfigMap
    current_corefile = _get_current_corefile()
    if current_corefile is None:
        logger.warning("Could not retrieve CoreDNS ConfigMap, skipping rewrite configuration")
        return

    # Build the ingress service FQDN
    ingress_fqdn = f"ingress-nginx-controller.{ingress_namespace}.svc.cluster.local"

    # Generate the new Corefile with rewrite rules
    new_corefile = _add_rewrite_rules(current_corefile, config.domains, ingress_fqdn)

    if new_corefile == current_corefile:
        logger.info("CoreDNS already configured with rewrite rules")
        return

    # Update the ConfigMap
    _update_coredns_configmap(new_corefile)

    # Restart CoreDNS to apply changes
    _restart_coredns()

    logger.info("CoreDNS configured successfully for in-cluster domain resolution")


def _all_domains_have_rewrite_rules(domains: list[str], corefile: str) -> bool:
    """Check if all domains have rewrite rules in the Corefile."""
    for domain in domains:
        escaped_domain = domain.replace(".", r"\.")
        if f".{escaped_domain}" not in corefile:
            return False
    return True


def check_coredns_rewrite_configured(config: CoreDnsRewriteConfig) -> bool:
    """
    Check if CoreDNS rewrite rules are already configured.

    Args:
        config (CoreDnsRewriteConfig): CoreDNS rewrite configuration

    Returns:
        bool: True if all domains have rewrite rules configured, False otherwise

    """
    if not config.enabled or not config.domains:
        return True  # Disabled or no domains means "configured" (nothing to do)

    current_corefile = _get_current_corefile()
    if current_corefile is None or LOCALARGO_MARKER_START not in current_corefile:
        return False

    return _all_domains_have_rewrite_rules(config.domains, current_corefile)


def _get_current_corefile() -> str | None:
    """Get the current Corefile content from CoreDNS ConfigMap."""
    try:
        kubectl_path = ensure_kubectl_available()
        result = run_subprocess(
            [
                kubectl_path,
                "get",
                "configmap",
                COREDNS_CONFIGMAP_NAME,
                "-n",
                COREDNS_NAMESPACE,
                "-o",
                "jsonpath={.data.Corefile}",
            ],
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.warning("Failed to get CoreDNS ConfigMap: %s", e)
        return None


def _add_rewrite_rules(corefile: str, domains: list[str], ingress_fqdn: str) -> str:
    """
    Add rewrite rules to the Corefile for the specified domains.

    The rewrite rules are added just before the closing brace of the main
    server block, after any existing plugins.

    Args:
        corefile (str): Current Corefile content
        domains (list[str]): List of domains to add rewrite rules for
        ingress_fqdn (str): FQDN of the ingress service

    Returns:
        str: Updated Corefile content with rewrite rules

    """
    # First, remove any existing localargo rewrite rules
    corefile = _remove_existing_rewrite_rules(corefile)

    # Build the rewrite rules block
    rewrite_lines = [f"        {LOCALARGO_MARKER_START}"]
    for domain in domains:
        # Escape dots for regex pattern
        escaped_domain = domain.replace(".", r"\.")
        # Add rewrite rule that matches *.domain (e.g. foo.localtest.me)
        # The 'answer auto' suffix rewrites the answer name back to the original query,
        # which is required for glibc-based resolvers (Python, curl, etc.)
        rewrite_lines.append(
            f"        rewrite name regex (.*)\\.{escaped_domain} {ingress_fqdn} answer auto",
        )
    rewrite_lines.append(f"        {LOCALARGO_MARKER_END}")

    rewrite_block = "\n".join(rewrite_lines)

    # Find the position to insert the rewrite rules
    # We want to insert before the closing brace of the main server block
    # The main server block is typically ".:53 { ... }"
    lines = corefile.split("\n")
    result_lines = []

    # Find the last closing brace at the root level
    brace_depth = 0
    insertion_done = False

    for line in lines:
        stripped = line.strip()

        # Track brace depth
        brace_depth += stripped.count("{") - stripped.count("}")

        # Insert before the final closing brace of the main block
        if stripped == "}" and brace_depth == 0 and not insertion_done:
            # Insert rewrite rules before this closing brace
            result_lines.append(rewrite_block)
            insertion_done = True

        result_lines.append(line)

    return "\n".join(result_lines)


def _remove_existing_rewrite_rules(corefile: str) -> str:
    """Remove any existing localargo rewrite rules from the Corefile."""
    lines = corefile.split("\n")
    result_lines = []
    in_localargo_block = False

    for line in lines:
        stripped = line.strip()

        if LOCALARGO_MARKER_START in stripped:
            in_localargo_block = True
            continue

        if LOCALARGO_MARKER_END in stripped:
            in_localargo_block = False
            continue

        if not in_localargo_block:
            result_lines.append(line)

    return "\n".join(result_lines)


def _update_coredns_configmap(new_corefile: str) -> None:
    """Update the CoreDNS ConfigMap with the new Corefile content."""
    kubectl_path = ensure_kubectl_available()

    # Create the patch JSON
    patch = {"data": {"Corefile": new_corefile}}

    run_subprocess(
        [
            kubectl_path,
            "patch",
            "configmap",
            COREDNS_CONFIGMAP_NAME,
            "-n",
            COREDNS_NAMESPACE,
            "--type=merge",
            "-p",
            json.dumps(patch),
        ],
        check=True,
    )

    logger.info("Updated CoreDNS ConfigMap with rewrite rules")


def _restart_coredns() -> None:
    """Restart CoreDNS deployment to apply configuration changes."""
    kubectl_path = ensure_kubectl_available()

    # Use rollout restart to gracefully restart CoreDNS pods
    run_subprocess(
        [
            kubectl_path,
            "rollout",
            "restart",
            "deployment/coredns",
            "-n",
            COREDNS_NAMESPACE,
        ],
        check=True,
    )

    # Wait for the rollout to complete
    run_subprocess(
        [
            kubectl_path,
            "rollout",
            "status",
            "deployment/coredns",
            "-n",
            COREDNS_NAMESPACE,
            "--timeout=60s",
        ],
        check=True,
    )

    logger.info("CoreDNS restarted successfully")
