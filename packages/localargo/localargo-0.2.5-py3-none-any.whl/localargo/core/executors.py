# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
"""
Step executors for idempotent execution framework.

These functions perform the actual installation and configuration work.
They reuse logic from the existing up.py implementation.
"""
# pylint: disable=duplicate-code

from __future__ import annotations

import base64
import os
import secrets
from typing import TYPE_CHECKING, Any

from localargo.config.manifest import (
    SecretEntry,
    SecretValueFromEnv,
    SecretValueRandomBase64,
    SecretValueRandomHex,
    SecretValueSameAs,
    SecretValueSpec,
    SecretValueStatic,
)
from localargo.core.argocd import ArgoClient, RepoAddOptions
from localargo.core.ca import (
    configure_nginx_default_certificate,
    create_ca_infrastructure,
    create_ca_secret,
    create_wildcard_certificate,
    distribute_ca_to_app_namespaces,
    install_cert_manager,
)
from localargo.core.coredns import configure_coredns_rewrite
from localargo.core.k8s import apply_manifests, ensure_namespace, get_secret_data, upsert_secret
from localargo.logging import logger
from localargo.providers.registry import get_provider
from localargo.utils.proc import ProcessError

if TYPE_CHECKING:
    from localargo.config.manifest import UpManifest


def execute_cluster_creation(  # pylint: disable=unused-argument
    manifest: UpManifest,
    client: ArgoClient | None = None,  # noqa: ARG001
) -> None:
    """Create the Kubernetes cluster."""
    cluster = manifest.clusters[0]
    provider_cls = get_provider(cluster.provider)
    provider = provider_cls(name=cluster.name)
    logger.info("Creating cluster '%s' with provider '%s'...", cluster.name, cluster.provider)
    success = provider.create_cluster(**cluster.kwargs)
    if not success:
        msg = f"Failed to create cluster '{cluster.name}' with provider '{cluster.provider}'"
        raise RuntimeError(msg)


def execute_argocd_installation(  # pylint: disable=unused-argument
    _manifest: UpManifest,
    _client: ArgoClient | None = None,
) -> None:
    """Install ArgoCD (this is handled by the cluster provider during creation)."""
    # ArgoCD installation is actually handled by the cluster provider
    # during cluster creation, so this executor is mostly a no-op.
    # The real work happens in the provider's create_cluster method.
    logger.info("ArgoCD installation is handled by cluster provider")


def execute_nginx_installation(  # pylint: disable=unused-argument
    manifest: UpManifest,  # noqa: ARG001
    client: ArgoClient | None = None,  # noqa: ARG001
) -> None:
    """Install nginx-ingress (this is handled by the cluster provider during creation)."""
    # Nginx ingress installation is handled by the cluster provider
    # during cluster creation, so this executor is mostly a no-op.
    # The real work happens in the provider's create_cluster method.
    logger.info("Nginx ingress installation is handled by cluster provider")


def _resolve_secret_value(spec: SecretValueSpec) -> str:
    """Resolve a secret value specification to its actual string value."""
    if isinstance(spec, SecretValueFromEnv):
        return os.environ.get(spec.from_env, "")
    if isinstance(spec, SecretValueRandomBase64):
        random_bytes = secrets.token_bytes(spec.num_bytes)
        return base64.b64encode(random_bytes).decode("ascii")
    if isinstance(spec, SecretValueRandomHex):
        return secrets.token_hex(spec.num_bytes)
    if isinstance(spec, SecretValueStatic):
        return spec.value
    if isinstance(spec, SecretValueSameAs):
        return _resolve_same_as_value(spec)
    # Should never happen with proper typing
    msg = f"Unknown secret value type: {type(spec)}"
    raise TypeError(msg)


def _resolve_same_as_value(spec: SecretValueSameAs) -> str:
    """Resolve a sameAs secret value by reading from another secret."""
    jsonpath = f"jsonpath={{.data.{spec.secret_key}}}"
    encoded_value = get_secret_data(spec.namespace, spec.secret_name, jsonpath)
    if not encoded_value:
        msg = f"Secret '{spec.secret_name}' key '{spec.secret_key}' not found in namespace '{spec.namespace}'"
        raise ValueError(msg)
    # The value is base64-encoded in Kubernetes secrets, decode it
    return base64.b64decode(encoded_value).decode("utf-8")


def _has_same_as_value(sec: SecretEntry) -> bool:
    """Check if a secret entry has any sameAs value specifications."""
    return any(isinstance(v, SecretValueSameAs) for v in sec.secret_value)


def _partition_secrets(
    secrets_list: list[SecretEntry],
) -> tuple[list[SecretEntry], list[SecretEntry]]:
    """Partition secrets into regular and sameAs groups."""
    regular = [sec for sec in secrets_list if not _has_same_as_value(sec)]
    same_as = [sec for sec in secrets_list if _has_same_as_value(sec)]
    return regular, same_as


def _add_secret_to_group(
    sec: SecretEntry,
    secret_groups: dict[tuple[str, str], dict[str, str]],
) -> None:
    """Add a secret entry's key-value to the appropriate group."""
    key = (sec.namespace, sec.secret_name)
    if key not in secret_groups:
        secret_groups[key] = {}
    # Add this key-value to the secret (use first matching value spec)
    for v in sec.secret_value:
        secret_groups[key][sec.secret_key] = _resolve_secret_value(v)
        break  # Only use the first value spec


def _group_secrets_by_target(
    secrets_list: list[SecretEntry],
) -> dict[tuple[str, str], dict[str, str]]:
    """Group secrets by (namespace, secret_name) and resolve their values."""
    secret_groups: dict[tuple[str, str], dict[str, str]] = {}
    for sec in secrets_list:
        _add_secret_to_group(sec, secret_groups)
    return secret_groups


def _apply_secret_groups(secret_groups: dict[tuple[str, str], dict[str, str]]) -> None:
    """Create/update secrets from grouped data."""
    for (namespace, secret_name), env_map in secret_groups.items():
        ensure_namespace(namespace)
        upsert_secret(namespace, secret_name, env_map)
        logger.info(
            "Created/updated secret '%s' in namespace '%s' with %d key(s)",
            secret_name,
            namespace,
            len(env_map),
        )


def _process_secret_batch(secrets_list: list[SecretEntry]) -> None:
    """Group and apply a batch of secrets."""
    if not secrets_list:
        return
    groups = _group_secrets_by_target(secrets_list)
    _apply_secret_groups(groups)


def execute_secrets_creation(  # pylint: disable=unused-argument
    manifest: UpManifest,
    client: ArgoClient | None = None,  # noqa: ARG001
) -> None:
    """
    Create/update Kubernetes secrets.

    Groups secrets by (namespace, secret_name) to ensure all keys are included
    when multiple manifest entries reference the same secret.

    Handles sameAs secrets by processing them after regular secrets, allowing
    them to reference values from secrets created earlier in the process.
    """
    regular_secrets, same_as_secrets = _partition_secrets(manifest.secrets)
    # Process regular secrets first, then sameAs (which may depend on regular)
    _process_secret_batch(regular_secrets)
    _process_secret_batch(same_as_secrets)


def execute_repo_creds_setup(manifest: UpManifest, client: ArgoClient | None = None) -> None:
    """Add repository credentials to ArgoCD."""
    if not client:
        msg = "ArgoCD client required for repo credentials setup"
        raise ValueError(msg)

    for rc in manifest.repo_creds:
        logger.info("Adding repo creds for %s", rc.repo_url)
        client.add_repo_cred(
            repo_url=rc.repo_url,
            username=rc.username,
            password=rc.password,
            options=RepoAddOptions(
                repo_type=getattr(rc, "type", "git"),
                enable_oci=getattr(rc, "enable_oci", False),
                description=getattr(rc, "description", None),
                name=getattr(rc, "name", None),
            ),
        )


def execute_apps_deployment(manifest: UpManifest, client: ArgoClient | None = None) -> None:
    """Create/update and sync ArgoCD applications."""
    if not client:
        msg = "ArgoCD client required for application deployment"
        raise ValueError(msg)

    for app in manifest.apps:
        # Ensure destination namespace exists prior to ArgoCD applying resources
        if getattr(app, "namespace", None):
            ensure_namespace(app.namespace)

        # If app_file provided, apply Application YAML directly; otherwise use CLI
        if getattr(app, "app_file", None):
            apply_manifests([str(app.app_file)])
            # Rely on Application's sync policy; skip CLI sync to avoid RBAC issues
            logger.info("Applied application manifest for '%s'", app.name)
            continue

        _create_or_update_app(client, app)
        client.sync_app(app.name, wait=True)
        logger.info("Created/updated and synced application '%s'", app.name)


def _create_or_update_app(client: ArgoClient, app: Any) -> None:  # noqa: ANN401
    """Create or update an ArgoCD application."""
    create_args = _build_app_args(app, create=True)
    try:
        client.run_with_auth(create_args)
    except ProcessError:  # update on existence or other benign failures
        update_args = _build_app_args(app, create=False)
        try:
            client.run_with_auth(update_args)
        except ProcessError:
            logger.error(
                "Failed to create or update app '%s'.\nCreate args: %s\nUpdate args: %s",
                app.name,
                " ".join(create_args),
                " ".join(update_args),
            )
            raise


def _build_app_args(app: Any, *, create: bool) -> list[str]:  # noqa: ANN401
    """Build argocd app create/update command arguments."""
    base = ["argocd", "app", "create" if create else "set", app.name]
    _append_repo_path_classic(base, app)
    _append_destination(base, app)
    _append_revision_and_helm(base, app)
    return base


def _append_repo_path_classic(base: list[str], app: Any) -> None:  # noqa: ANN401
    """Append repo and path arguments for classic app creation."""
    sources = getattr(app, "sources", None) or []
    # Use first source only; older argocd CLI lacks --source support
    if sources:
        s = sources[0]
        repo = getattr(s, "repo_url", app.repo_url)
        path = getattr(s, "path", app.path)
        chart = getattr(s, "chart", None)
        base.extend(["--repo", repo])
        if chart:
            base.extend(["--helm-chart", chart])
        else:
            base.extend(["--path", path or "."])
        # Merge helm flags from the source into top-level handling
        _append_source_helm_filtered(base, getattr(s, "helm", None), is_chart=bool(chart))
        # Prefer source revision over top-level when provided
        if getattr(s, "target_revision", None):
            # Prefer source-specified revision; _append_revision_and_helm will use this
            app.target_revision = s.target_revision
        return
    base.extend(["--repo", app.repo_url, "--path", app.path])


def _append_destination(base: list[str], app: Any) -> None:  # noqa: ANN401
    """Append destination arguments."""
    base.extend(
        [
            "--dest-server",
            "https://kubernetes.default.svc",
            "--dest-namespace",
            getattr(app, "namespace", "default"),
        ],
    )


def _append_revision_and_helm(base: list[str], app: Any) -> None:  # noqa: ANN401
    """Append revision and helm arguments."""
    # Ensure single --revision occurrence
    base.extend(["--revision", app.target_revision])
    # If sources exist, we already appended any per-source helm flags; avoid duplicates
    if getattr(app, "sources", None):
        return
    if getattr(app, "helm", None):
        if app.helm.release_name:
            base.extend(["--release-name", app.helm.release_name])
        for v in getattr(app.helm, "value_files", []) or []:
            base.extend(["--values", v])


def _append_source_helm_filtered(base: list[str], hcfg: Any | None, *, is_chart: bool) -> None:  # noqa: ANN401
    """Append helm configuration from source, filtered for chart compatibility."""
    if hcfg and getattr(hcfg, "release_name", None):
        base.extend(["--release-name", hcfg.release_name])
    if hcfg and getattr(hcfg, "value_files", None):
        for v in _filter_values_for_chart(hcfg.value_files, is_chart=is_chart):
            base.extend(["--values", v])


def _filter_values_for_chart(values: list[str], *, is_chart: bool) -> list[str]:
    """Filter helm values for chart repos to avoid external or env paths."""
    if not is_chart:
        return list(values)
    return [v for v in values if v and "/" not in v and not v.startswith("$")]


# ------------------------
# CA Management Executors
# ------------------------
# These executors delegate to the ca.py module for clean separation of concerns.
# The ca.py module contains the actual CA infrastructure logic.


def execute_cert_manager_installation(
    _manifest: UpManifest,
    _client: ArgoClient | None = None,
) -> None:
    """Install cert-manager with CRDs."""
    install_cert_manager()


def execute_ca_setup(
    manifest: UpManifest,
    _client: ArgoClient | None = None,
) -> None:
    """
    Set up dev Root CA and certificates.

    This orchestrates the complete CA setup:
    1. Create CA infrastructure (self-signed issuer -> root CA -> CA issuer)
    2. Issue wildcard certificate for *.localtest.me
    3. Configure nginx-ingress to use the wildcard certificate
    4. Create CA secret for workloads to trust
    """
    logger.info("Setting up dev Root CA and certificates")
    ingress_config = manifest.ingress

    # Create CA infrastructure (self-signed issuer -> root CA cert -> CA issuer)
    create_ca_infrastructure()

    # Create wildcard certificate for *.localtest.me
    create_wildcard_certificate(ingress_config.namespace)

    # Configure nginx-ingress to use the wildcard certificate as default
    configure_nginx_default_certificate(ingress_config.namespace)

    # Create CA secret for workloads to use for trust
    create_ca_secret(ingress_config)

    logger.info("CA setup completed successfully")


# ------------------------
# CoreDNS Configuration Executor
# ------------------------


def execute_coredns_setup(
    manifest: UpManifest,
    _client: ArgoClient | None = None,
) -> None:
    """
    Configure CoreDNS for in-cluster domain resolution.

    This adds rewrite rules to CoreDNS so that pods inside the cluster can
    resolve *.localtest.me (and other configured domains) to the ingress-nginx
    service instead of 127.0.0.1.

    This is essential for OIDC/OAuth flows where backend services need to
    call identity providers using the same hostnames as browsers.
    """
    ingress_config = manifest.ingress
    coredns_config = ingress_config.coredns_rewrite

    if not coredns_config.enabled:
        logger.info("CoreDNS rewrite is disabled, skipping")
        return

    if not coredns_config.domains:
        logger.info("No domains configured for CoreDNS rewrite, skipping")
        return

    configure_coredns_rewrite(coredns_config, ingress_config.namespace)


# ------------------------
# CA Distribution Executor
# ------------------------


def _log_distribution_results(results: dict[str, bool]) -> None:
    """Log the results of CA distribution."""
    if not results:
        return
    success_count = sum(1 for success in results.values() if success)
    logger.info("CA distribution complete: %d/%d namespaces", success_count, len(results))


def execute_ca_distribution(
    manifest: UpManifest,
    _client: ArgoClient | None = None,
) -> None:
    """
    Distribute the CA secret to all app namespaces.

    This copies the CA certificate secret from the ingress namespace to each
    app namespace, enabling applications to trust the local dev CA for TLS
    connections (e.g., OIDC callbacks to identity providers).
    """
    app_namespaces = [app.namespace for app in manifest.apps if app.namespace]

    if not app_namespaces:
        logger.info("No app namespaces to distribute CA secret to")
        return

    results = distribute_ca_to_app_namespaces(app_namespaces, manifest.ingress)
    _log_distribution_results(results)
