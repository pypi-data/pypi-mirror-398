# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
"""
Certificate Authority management for localargo.

This module provides functionality to create a dev Root CA using cert-manager,
issue wildcard certificates for *.localtest.me, and configure nginx-ingress
to use the wildcard certificate as default.

CA Architecture:
    1. Self-signed ClusterIssuer (bootstrap)
    2. Root CA Certificate (issued by self-signed issuer)
    3. CA ClusterIssuer (uses root CA secret)
    4. Wildcard Certificate (issued by CA ClusterIssuer)
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

from localargo.core.k8s import ensure_namespace
from localargo.logging import logger
from localargo.utils.cli import (
    ensure_helm_available,
    ensure_kubectl_available,
    run_subprocess,
)

if TYPE_CHECKING:
    from localargo.config.manifest import IngressConfig

# =============================================================================
# Constants
# =============================================================================

INGRESS_ROOT_DOMAIN = "localtest.me"

# Resource names
SELF_SIGNED_ISSUER_NAME = "localargo-selfsigned-issuer"
ROOT_CA_CERT_NAME = "localargo-root-ca"
ROOT_CA_SECRET_NAME = "localargo-root-ca-secret"
CA_CLUSTER_ISSUER_NAME = "localargo-ca-issuer"
WILDCARD_CERT_NAME = "localargo-wildcard-cert"
WILDCARD_SECRET_NAME = "localargo-wildcard-tls"

# Helm chart settings
CERT_MANAGER_NAMESPACE = "cert-manager"
CERT_MANAGER_CHART = "jetstack/cert-manager"
JETSTACK_REPO_URL = "https://charts.jetstack.io"


# =============================================================================
# Helper utilities
# =============================================================================


@dataclass(frozen=True)
class ToolPaths:
    """Container for validated tool paths."""

    kubectl: str
    helm: str


def get_tool_paths() -> ToolPaths:
    """Get validated paths for kubectl and helm."""
    kubectl = ensure_kubectl_available()
    helm = ensure_helm_available()

    return ToolPaths(kubectl=kubectl, helm=helm)


def run_kubectl(
    args: list[str],
    *,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a kubectl command with consistent error handling."""
    tools = get_tool_paths()
    cmd = [tools.kubectl, *args]
    return run_subprocess(cmd, check=check, capture_output=capture_output)


def run_helm(args: list[str], *, check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a helm command with consistent error handling."""
    tools = get_tool_paths()
    cmd = [tools.helm, *args]
    return run_subprocess(cmd, check=check, capture_output=capture_output)


def apply_yaml(yaml_content: str) -> None:
    """Apply YAML content to the cluster."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_file = f.name

    try:
        run_kubectl(["apply", "-f", yaml_file])
    finally:
        Path(yaml_file).unlink(missing_ok=True)


def wait_for_condition(
    resource: str,
    condition: str,
    *,
    namespace: str | None = None,
    timeout: str = "120s",
) -> None:
    """Wait for a Kubernetes resource to reach a condition."""
    args = ["wait", f"--for=condition={condition}", resource, f"--timeout={timeout}"]
    if namespace:
        args.extend(["-n", namespace])
    run_kubectl(args)


def resource_exists(resource_type: str, name: str, *, namespace: str | None = None) -> bool:
    """Check if a Kubernetes resource exists."""
    args = ["get", resource_type, name]
    if namespace:
        args.extend(["-n", namespace])
    try:
        run_kubectl(args, capture_output=True)
    except subprocess.CalledProcessError:
        return False
    else:
        return True


# =============================================================================
# cert-manager installation
# =============================================================================


def install_cert_manager() -> None:
    """Install cert-manager using Helm."""
    logger.info("Installing cert-manager")

    # Add jetstack helm repo
    run_helm(["repo", "add", "jetstack", JETSTACK_REPO_URL], capture_output=True)
    run_helm(["repo", "update"], capture_output=True)

    # Install cert-manager with CRDs
    run_helm(
        [
            "upgrade",
            "--install",
            "cert-manager",
            CERT_MANAGER_CHART,
            "--namespace",
            CERT_MANAGER_NAMESPACE,
            "--create-namespace",
            "--wait",
            "--wait-for-jobs",
            "--timeout=300s",
            "--set",
            "installCRDs=true",
        ],
    )

    # Wait for cert-manager deployments to be ready
    wait_for_condition(
        "deployment/cert-manager",
        "available",
        namespace=CERT_MANAGER_NAMESPACE,
        timeout="300s",
    )
    wait_for_condition(
        "deployment/cert-manager-webhook",
        "available",
        namespace=CERT_MANAGER_NAMESPACE,
        timeout="300s",
    )
    wait_for_condition(
        "deployment/cert-manager-cainjector",
        "available",
        namespace=CERT_MANAGER_NAMESPACE,
        timeout="300s",
    )

    logger.info("cert-manager installed successfully")


# =============================================================================
# CA creation
# =============================================================================


def create_ca_infrastructure() -> None:
    """
    Create the complete CA infrastructure.

    This creates:
    1. A self-signed ClusterIssuer (for bootstrapping)
    2. A root CA certificate (issued by the self-signed issuer)
    3. A CA ClusterIssuer (that uses the root CA secret to issue certs)
    """
    logger.info("Creating CA infrastructure")

    # Step 1: Create self-signed ClusterIssuer
    _create_self_signed_issuer()

    # Step 2: Create root CA certificate
    _create_root_ca_certificate()

    # Step 3: Create CA ClusterIssuer that uses the root CA
    _create_ca_cluster_issuer()

    logger.info("CA infrastructure created successfully")


def _create_self_signed_issuer() -> None:
    """Create a self-signed ClusterIssuer for bootstrapping."""
    if resource_exists("clusterissuer", SELF_SIGNED_ISSUER_NAME):
        logger.info("Self-signed ClusterIssuer already exists")
        return

    yaml = f"""\
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: {SELF_SIGNED_ISSUER_NAME}
spec:
  selfSigned: {{}}
"""
    apply_yaml(yaml)
    logger.info("Created self-signed ClusterIssuer: %s", SELF_SIGNED_ISSUER_NAME)


def _create_root_ca_certificate() -> None:
    """Create the root CA certificate."""
    if resource_exists("certificate", ROOT_CA_CERT_NAME, namespace=CERT_MANAGER_NAMESPACE):
        logger.info("Root CA certificate already exists")
        return

    yaml = f"""\
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: {ROOT_CA_CERT_NAME}
  namespace: {CERT_MANAGER_NAMESPACE}
spec:
  isCA: true
  commonName: localargo-dev-ca
  secretName: {ROOT_CA_SECRET_NAME}
  duration: 87600h  # 10 years
  renewBefore: 8760h  # 1 year
  privateKey:
    algorithm: ECDSA
    size: 256
  issuerRef:
    name: {SELF_SIGNED_ISSUER_NAME}
    kind: ClusterIssuer
    group: cert-manager.io
"""
    apply_yaml(yaml)

    # Wait for the certificate to be ready
    wait_for_condition(
        f"certificate/{ROOT_CA_CERT_NAME}",
        "ready",
        namespace=CERT_MANAGER_NAMESPACE,
        timeout="120s",
    )
    logger.info("Created root CA certificate: %s", ROOT_CA_CERT_NAME)


def _create_ca_cluster_issuer() -> None:
    """Create a ClusterIssuer that uses the root CA to issue certificates."""
    if resource_exists("clusterissuer", CA_CLUSTER_ISSUER_NAME):
        logger.info("CA ClusterIssuer already exists")
        return

    yaml = f"""\
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: {CA_CLUSTER_ISSUER_NAME}
spec:
  ca:
    secretName: {ROOT_CA_SECRET_NAME}
"""
    apply_yaml(yaml)
    logger.info("Created CA ClusterIssuer: %s", CA_CLUSTER_ISSUER_NAME)


# =============================================================================
# Wildcard certificate
# =============================================================================


def create_wildcard_certificate(ingress_namespace: str) -> None:
    """Create a wildcard certificate for *.localtest.me."""
    logger.info("Creating wildcard certificate for *.%s", INGRESS_ROOT_DOMAIN)

    # Ensure the ingress namespace exists
    ensure_namespace(ingress_namespace)

    if resource_exists("certificate", WILDCARD_CERT_NAME, namespace=ingress_namespace):
        logger.info("Wildcard certificate already exists")
        return

    yaml = f"""\
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: {WILDCARD_CERT_NAME}
  namespace: {ingress_namespace}
spec:
  secretName: {WILDCARD_SECRET_NAME}
  duration: 2160h  # 90 days
  renewBefore: 360h  # 15 days
  privateKey:
    algorithm: ECDSA
    size: 256
  issuerRef:
    name: {CA_CLUSTER_ISSUER_NAME}
    kind: ClusterIssuer
    group: cert-manager.io
  dnsNames:
    - "*.{INGRESS_ROOT_DOMAIN}"
    - "{INGRESS_ROOT_DOMAIN}"
"""
    apply_yaml(yaml)

    # Wait for the certificate to be ready
    wait_for_condition(
        f"certificate/{WILDCARD_CERT_NAME}",
        "ready",
        namespace=ingress_namespace,
        timeout="120s",
    )
    logger.info("Created wildcard certificate: %s", WILDCARD_CERT_NAME)


# =============================================================================
# nginx-ingress configuration
# =============================================================================


def configure_nginx_default_certificate(ingress_namespace: str) -> None:
    """Configure nginx-ingress to use the wildcard certificate as default."""
    logger.info("Configuring nginx-ingress default certificate")

    controller_name = "ingress-nginx-controller"
    resource_kind = _find_nginx_controller_kind(ingress_namespace, controller_name)

    if resource_kind is None:
        logger.warning(
            "nginx-ingress controller not found in namespace '%s'. Skipping default certificate configuration.",
            ingress_namespace,
        )
        return

    desired_arg = f"--default-ssl-certificate={ingress_namespace}/{WILDCARD_SECRET_NAME}"

    # Check current args
    current_args = _get_container_args(resource_kind, controller_name, ingress_namespace)

    if desired_arg in current_args:
        logger.info("nginx-ingress already configured with default certificate")
        return

    # Patch the controller to add the argument
    patch = [{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": desired_arg}]

    run_kubectl(
        [
            "patch",
            resource_kind,
            controller_name,
            "-n",
            ingress_namespace,
            "--type=json",
            "-p",
            json.dumps(patch),
        ],
    )

    logger.info("Configured nginx-ingress to use wildcard certificate")


def _find_nginx_controller_kind(namespace: str, name: str) -> str | None:
    """Find whether nginx controller is a Deployment or DaemonSet."""
    if resource_exists("deployment", name, namespace=namespace):
        return "deployment"
    if resource_exists("daemonset", name, namespace=namespace):
        return "daemonset"
    return None


def _get_container_args(resource_kind: str, name: str, namespace: str) -> list[str]:
    """Get the current container args for a workload."""
    try:
        result = run_kubectl(
            [
                "get",
                resource_kind,
                name,
                "-n",
                namespace,
                "-o=jsonpath={.spec.template.spec.containers[0].args}",
            ],
            capture_output=True,
        )
        if result.stdout.strip():
            return cast("list[str]", json.loads(result.stdout.strip()))
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        pass
    return []


# =============================================================================
# CA trust distribution
# =============================================================================


def create_ca_secret(ingress_config: IngressConfig) -> None:
    """Create a secret containing the CA certificate for workloads to trust."""
    logger.info("Creating CA trust secret")

    ensure_namespace(ingress_config.namespace)

    # Get the CA certificate from the root CA secret
    result = run_kubectl(
        [
            "get",
            f"secret/{ROOT_CA_SECRET_NAME}",
            "-n",
            CERT_MANAGER_NAMESPACE,
            "-o",
            "jsonpath={.data.ca\\.crt}",
        ],
        capture_output=True,
    )

    ca_cert_b64 = result.stdout.strip()
    if not ca_cert_b64:
        msg = "Failed to retrieve CA certificate from root CA secret"
        raise RuntimeError(msg)

    # Create the user-facing secret
    yaml = f"""\
apiVersion: v1
kind: Secret
metadata:
  name: {ingress_config.secret_name}
  namespace: {ingress_config.namespace}
type: Opaque
data:
  {ingress_config.secret_key}: {ca_cert_b64}
"""
    apply_yaml(yaml)
    logger.info(
        "Created CA secret '%s' in namespace '%s'",
        ingress_config.secret_name,
        ingress_config.namespace,
    )


# =============================================================================
# CA distribution to app namespaces
# =============================================================================


def get_app_namespaces_needing_ca(app_namespaces: list[str], ingress_namespace: str) -> list[str]:
    """
    Get list of app namespaces that need the CA secret.

    Filters out the ingress namespace (already has it) and returns unique namespaces.

    Args:
        app_namespaces (list[str]): List of namespaces from apps configuration.
        ingress_namespace (str): The ingress-nginx namespace (source of CA secret).

    Returns:
        list[str]: List of unique namespaces that need the CA secret distributed.

    """
    # Use dict to preserve order while deduplicating
    unique = dict.fromkeys(ns for ns in app_namespaces if ns and ns != ingress_namespace)
    return list(unique.keys())


def check_ca_secret_in_namespace(namespace: str, secret_name: str) -> bool:
    """
    Check if the CA secret exists in the specified namespace.

    Args:
        namespace (str): The namespace to check.
        secret_name (str): The name of the CA secret.

    Returns:
        bool: True if the secret exists, False otherwise.

    """
    return resource_exists("secret", secret_name, namespace=namespace)


def distribute_ca_to_namespace(
    namespace: str,
    ingress_config: IngressConfig,
) -> None:
    """
    Copy the CA secret to a specific namespace.

    Args:
        namespace (str): The target namespace to copy the CA secret to.
        ingress_config (IngressConfig): Ingress configuration containing secret details.

    Raises:
        RuntimeError: If the CA certificate cannot be retrieved from the source secret.

    """
    logger.info("Distributing CA secret to namespace '%s'", namespace)

    # Ensure namespace exists
    ensure_namespace(namespace)

    # Get the CA certificate from the source secret
    result = run_kubectl(
        [
            "get",
            f"secret/{ingress_config.secret_name}",
            "-n",
            ingress_config.namespace,
            "-o",
            f"jsonpath={{.data.{ingress_config.secret_key}}}",
        ],
        capture_output=True,
    )

    ca_cert_b64 = result.stdout.strip()
    if not ca_cert_b64:
        msg = f"Failed to retrieve CA certificate from {ingress_config.namespace}/{ingress_config.secret_name}"
        raise RuntimeError(msg)

    # Create the secret in the target namespace
    yaml = f"""\
apiVersion: v1
kind: Secret
metadata:
  name: {ingress_config.secret_name}
  namespace: {namespace}
  labels:
    app.kubernetes.io/managed-by: localargo
    localargo.dev/ca-distribution: "true"
type: Opaque
data:
  {ingress_config.secret_key}: {ca_cert_b64}
"""
    apply_yaml(yaml)
    logger.info("Created CA secret '%s' in namespace '%s'", ingress_config.secret_name, namespace)


def distribute_ca_to_app_namespaces(
    app_namespaces: list[str],
    ingress_config: IngressConfig,
) -> dict[str, bool]:
    """
    Distribute the CA secret to all app namespaces that need it.

    Args:
        app_namespaces (list[str]): List of namespaces from apps configuration.
        ingress_config (IngressConfig): Ingress configuration with namespace and secret details.

    Returns:
        dict[str, bool]: Dictionary mapping namespace to success status.

    """
    namespaces_needing_ca = get_app_namespaces_needing_ca(app_namespaces, ingress_config.namespace)

    if not namespaces_needing_ca:
        logger.info("No app namespaces need CA distribution")
        return {}

    results: dict[str, bool] = {}

    for namespace in namespaces_needing_ca:
        try:
            # Check if already exists
            if check_ca_secret_in_namespace(namespace, ingress_config.secret_name):
                logger.info("CA secret already exists in namespace '%s'", namespace)
                results[namespace] = True
                continue

            distribute_ca_to_namespace(namespace, ingress_config)
            results[namespace] = True
        except (subprocess.CalledProcessError, RuntimeError) as e:
            logger.error("Failed to distribute CA to namespace '%s': %s", namespace, e)
            results[namespace] = False

    return results


# =============================================================================
# Main orchestration
# =============================================================================


def setup_ca(ingress_config: IngressConfig) -> None:
    """Complete CA setup: install cert-manager, create CA, issue wildcard cert."""
    logger.info("Setting up Certificate Authority infrastructure")

    # 1. Install cert-manager
    install_cert_manager()

    # 2. Create CA infrastructure
    create_ca_infrastructure()

    # 3. Create wildcard certificate
    create_wildcard_certificate(ingress_config.namespace)

    # 4. Configure nginx to use wildcard cert
    configure_nginx_default_certificate(ingress_config.namespace)

    # 5. Create CA secret for workloads
    create_ca_secret(ingress_config)

    logger.info("CA setup completed successfully")
