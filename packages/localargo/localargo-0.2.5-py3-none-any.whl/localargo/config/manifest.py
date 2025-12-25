# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
"""
Extended up-manifest loader and validator.

This module supports the extended up-manifest schema used by `localargo up`,
`localargo validate`, and `localargo down` commands with top-level keys:
'cluster', 'apps', 'repo_creds', 'secrets'.

The manifest is parsed into dataclasses with validation helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from localargo.providers.registry import get_provider

try:  # type: ignore[unused-ignore]
    import yaml
except ImportError:  # pragma: no cover - handled at runtime
    yaml = None  # type: ignore[assignment]


class ManifestError(Exception):
    """Base exception for manifest-related errors."""


class ManifestValidationError(ManifestError):
    """Raised when manifest validation fails."""


@dataclass
class ClusterConfig:
    """
    Configuration for a single cluster.

    Args:
        name (str): Name of the cluster.
        provider (str): Name of the cluster provider.
        **kwargs (Any): Additional provider-specific configuration.

    Attributes:
        name (str): Name of the cluster.
        provider (str): Name of the cluster provider.
        kwargs (dict[str, Any]): Additional provider-specific configuration.

    """

    name: str
    provider: str
    kwargs: dict[str, Any] = field(default_factory=dict)

    def __init__(self, name: str, provider: str, **kwargs: Any) -> None:  # noqa: ANN401
        self.name = name
        self.provider = provider
        self.kwargs = kwargs

    def __repr__(self) -> str:
        """Return a string representation of the cluster configuration."""
        kwargs_str = f", kwargs={self.kwargs!r}" if self.kwargs else ""
        return f"ClusterConfig(name={self.name!r}, provider={self.provider!r}{kwargs_str})"


def _validate_cluster_data_type(cluster_data: Any, index: int) -> None:  # noqa: ANN401
    """Validate that cluster data is a dictionary."""
    if not isinstance(cluster_data, dict):
        msg = f"Cluster {index} must be a dictionary"
        raise ManifestValidationError(msg)


def _validate_required_fields(cluster_data: dict[str, Any], index: int) -> None:
    """Validate that required fields are present."""
    if "name" not in cluster_data:
        msg = f"Cluster {index} missing required 'name' field"
        raise ManifestValidationError(msg)

    if "provider" not in cluster_data:
        msg = f"Cluster {index} missing required 'provider' field"
        raise ManifestValidationError(msg)


def _validate_field_types(name: Any, provider_name: Any, index: int) -> None:  # noqa: ANN401
    """Validate that name and provider fields are strings."""
    if not isinstance(name, str):
        msg = f"Cluster {index} 'name' must be a string"
        raise ManifestValidationError(msg)

    if not isinstance(provider_name, str):
        msg = f"Cluster {index} 'provider' must be a string"
        raise ManifestValidationError(msg)


def _validate_provider_exists(provider_name: str, index: int) -> None:
    """Validate that the provider exists."""
    try:
        get_provider(provider_name)
    except ValueError as e:
        msg = f"Cluster {index}: {e}"
        raise ManifestValidationError(msg) from e


def _parse_cluster_data(cluster_data: Any, index: int) -> ClusterConfig:  # noqa: ANN401
    """
    Parse individual cluster configuration.

    Args:
        cluster_data (Any): Cluster configuration data
        index (int): Cluster index for error reporting

    Returns:
        ClusterConfig: Parsed cluster configuration object

    """
    _validate_cluster_data_type(cluster_data, index)
    _validate_required_fields(cluster_data, index)

    name = cluster_data["name"]
    provider_name = cluster_data["provider"]

    _validate_field_types(name, provider_name, index)
    _validate_provider_exists(provider_name, index)

    kwargs = {k: v for k, v in cluster_data.items() if k not in ("name", "provider")}

    return ClusterConfig(name=name, provider=provider_name, **kwargs)


# ------------------------
# Extended up-manifest schema (cluster/apps/repo_creds/secrets)
# ------------------------


@dataclass
class AppHelmConfig:
    """Helm-specific options for an application entry."""

    release_name: str | None = None
    value_files: list[str] = field(default_factory=list)


@dataclass
class SourceSpec:
    """A single application source entry (git path or helm chart)."""

    repo_url: str
    target_revision: str = "HEAD"
    path: str | None = None
    chart: str | None = None
    ref: str | None = None
    helm: AppHelmConfig | None = None


@dataclass
class AppEntry:  # pylint: disable=too-many-instance-attributes
    """Application entry as defined in up-manifest 'apps' list."""

    name: str
    namespace: str
    app_file: str | None = None
    sources: list[SourceSpec] = field(default_factory=list)
    # Back-compat normalized single-source view for current CLI code paths
    repo_url: str = ""
    target_revision: str = "HEAD"
    path: str = "."
    helm: AppHelmConfig | None = None
    chart_name: str | None = None
    # reduce pylint instance-attribute warning by grouping extra computed fields
    _extras: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass
class RepoCredEntry:
    """Repository credential entry for ArgoCD access."""

    name: str
    repo_url: str
    username: str
    password: str
    type: str = "git"
    enable_oci: bool = False
    description: str | None = None


@dataclass
class SecretValueFromEnv:
    """Secret value sourced from an environment variable."""

    from_env: str


@dataclass
class SecretValueRandomBase64:
    """Secret value generated as random base64-encoded bytes."""

    num_bytes: int


@dataclass
class SecretValueRandomHex:
    """Secret value generated as random hex-encoded bytes."""

    num_bytes: int


@dataclass
class SecretValueStatic:
    """Secret value from a literal static string."""

    value: str


@dataclass
class SecretValueSameAs:
    """Secret value copied from another existing secret."""

    namespace: str
    secret_name: str
    secret_key: str


# Union type for secret value specifications
SecretValueSpec = (
    SecretValueFromEnv | SecretValueRandomBase64 | SecretValueRandomHex | SecretValueStatic | SecretValueSameAs
)


@dataclass
class SecretEntry:
    """Kubernetes secret specification to be created or updated."""

    name: str
    namespace: str
    secret_name: str
    secret_key: str
    secret_value: list[SecretValueSpec]


@dataclass
class CoreDnsRewriteConfig:
    """Configuration for CoreDNS rewrite rules to resolve ingress hostnames in-cluster."""

    enabled: bool = True
    domains: list[str] = field(default_factory=lambda: ["localtest.me"])


@dataclass
class IngressConfig:
    """Configuration for ingress and CA certificate management."""

    namespace: str = "ingress-nginx"
    secret_name: str = "localargo-ca-cert"
    secret_key: str = "crt"
    coredns_rewrite: CoreDnsRewriteConfig = field(default_factory=CoreDnsRewriteConfig)


@dataclass
class UpManifest:
    """Top-level up-manifest schema used by validate/up/down commands."""

    clusters: list[ClusterConfig]
    apps: list[AppEntry]
    repo_creds: list[RepoCredEntry]
    secrets: list[SecretEntry]
    ingress: IngressConfig = field(default_factory=IngressConfig)


def load_up_manifest(path: str | Path) -> UpManifest:
    """Load extended up-manifest matching provided YAML example."""
    p = Path(path)
    _ensure_manifest_file(p)
    raw = _load_yaml_mapping(p)
    clusters = _parse_clusters(raw.get("cluster") or [])
    apps = _parse_apps(raw.get("apps") or [], base_dir=p.parent)
    repocreds = _parse_repo_creds(raw.get("repo_creds") or [])
    secrets = _parse_secrets(raw.get("secrets") or [])
    ingress = _parse_ingress(raw.get("ingress"))
    return UpManifest(clusters=clusters, apps=apps, repo_creds=repocreds, secrets=secrets, ingress=ingress)


def _ensure_manifest_file(path: Path) -> None:
    if not path.exists():
        msg = f"Manifest file not found: {path}"
        raise ManifestError(msg)
    if yaml is None:
        msg = "PyYAML is required to load manifests. Install with: pip install PyYAML"
        raise ManifestError(msg)


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        msg = "Up-manifest must be a mapping"
        raise ManifestValidationError(msg)
    return data


def _parse_clusters(clusters_raw: Any) -> list[ClusterConfig]:  # noqa: ANN401
    if not isinstance(clusters_raw, list) or not clusters_raw:
        msg = "'cluster' must be a non-empty list"
        raise ManifestValidationError(msg)
    return [_parse_cluster_data(c, i) for i, c in enumerate(clusters_raw)]


def _parse_apps(apps_raw: Any, *, base_dir: Path) -> list[AppEntry]:  # noqa: ANN401
    if not isinstance(apps_raw, list):
        msg = "'apps' must be a list"
        raise ManifestValidationError(msg)
    result: list[AppEntry] = []
    for idx, item in enumerate(apps_raw):
        result.append(_parse_single_app(idx, item, base_dir=base_dir))
    return result


def _parse_single_app(idx: int, item: Any, *, base_dir: Path) -> AppEntry:  # noqa: ANN401
    name, spec_any = _coerce_single_key_mapping(item, f"apps[{idx}]")
    namespace = str(spec_any.get("namespace", "")).strip()
    if not namespace:
        msg = f"apps[{idx}].{name} missing required 'namespace' field"
        raise ManifestValidationError(msg)
    app_file_raw = spec_any.get("app_file")
    app_file: str | None = None
    if isinstance(app_file_raw, str) and app_file_raw.strip():
        # Resolve relative to manifest directory
        app_path = (base_dir / app_file_raw).resolve()
        app_file = str(app_path)
    sources = _parse_sources(idx, name, spec_any.get("sources"))
    if sources:
        return _normalize_first_source(name, namespace, sources, app_file)
    return _parse_single_source_fallback(name, namespace, spec_any, app_file)


def _parse_sources(idx: int, app_name: str, raw: Any) -> list[SourceSpec]:  # noqa: ANN401
    if not isinstance(raw, list) or not raw:
        return []
    return [_build_source_spec(idx, app_name, sidx, s) for sidx, s in enumerate(raw)]


def _build_source_spec(idx: int, app_name: str, sidx: int, s: Any) -> SourceSpec:  # noqa: ANN401
    if not isinstance(s, dict):
        msg = f"apps[{idx}].{app_name} sources[{sidx}] must be a mapping"
        raise ManifestValidationError(msg)
    repo_url = str(s.get("repoURL", ""))
    target_revision = str(s.get("targetRevision", "HEAD"))
    path_raw = s.get("path")
    chart_raw = s.get("chart")
    ref_raw = s.get("ref")
    path_val = None if path_raw is None else str(path_raw)
    chart_val = None if chart_raw is None else str(chart_raw)
    ref_val = None if ref_raw is None else str(ref_raw)
    helm_cfg = _parse_helm_config(s.get("helm"))
    return SourceSpec(
        repo_url=repo_url,
        target_revision=target_revision,
        path=path_val,
        chart=chart_val,
        ref=ref_val,
        helm=helm_cfg,
    )


def _normalize_first_source(
    name: str,
    namespace: str,
    sources: list[SourceSpec],
    app_file: str | None,
) -> AppEntry:
    first = sources[0]
    return AppEntry(
        name=name,
        namespace=namespace,
        app_file=app_file,
        sources=sources,
        repo_url=first.repo_url,
        target_revision=first.target_revision,
        path=first.path or ".",
        helm=first.helm,
        chart_name=first.chart,
    )


def _parse_single_source_fallback(
    name: str,
    namespace: str,
    spec_any: dict[str, Any],
    app_file: str | None,
) -> AppEntry:
    repo_url = str(spec_any.get("repoURL", ""))
    path_val = str(spec_any.get("path", "."))
    target_revision = str(spec_any.get("targetRevision", "HEAD"))
    helm_cfg = _parse_helm_config(spec_any.get("helm"))
    return AppEntry(
        name=name,
        namespace=namespace,
        app_file=app_file,
        sources=[],
        repo_url=repo_url,
        target_revision=target_revision,
        path=path_val,
        helm=helm_cfg,
        chart_name=None,
    )


def _parse_repo_creds(repocreds_raw: Any) -> list[RepoCredEntry]:  # noqa: ANN401
    if not isinstance(repocreds_raw, list):
        msg = "'repo_creds' must be a list"
        raise ManifestValidationError(msg)
    result: list[RepoCredEntry] = []
    for idx, item in enumerate(repocreds_raw):
        result.append(_parse_single_repo_cred(idx, item))
    return result


def _parse_single_repo_cred(idx: int, item: Any) -> RepoCredEntry:  # noqa: ANN401
    name, spec_any = _coerce_single_key_mapping(item, f"repo_creds[{idx}]")
    return RepoCredEntry(
        name=name,
        repo_url=str(spec_any.get("repoURL", "")),
        username=str(spec_any.get("username", "")),
        password=str(spec_any.get("password", "")),
        type=str(spec_any.get("type", "git")),
        enable_oci=bool(spec_any.get("enableOCI", False)),
        description=(str(spec_any.get("description")) if spec_any.get("description") is not None else None),
    )


def _parse_secrets(secrets_raw: Any) -> list[SecretEntry]:  # noqa: ANN401
    if not isinstance(secrets_raw, list):
        msg = "'secrets' must be a list"
        raise ManifestValidationError(msg)
    result: list[SecretEntry] = []
    for idx, item in enumerate(secrets_raw):
        result.append(_parse_single_secret(idx, item))
    return result


def _parse_single_secret(idx: int, item: Any) -> SecretEntry:  # noqa: ANN401
    name, spec_any = _coerce_single_key_mapping(item, f"secrets[{idx}]")
    vals = _parse_secret_values(spec_any.get("secretValue") or [])
    return SecretEntry(
        name=name,
        namespace=str(spec_any.get("namespace", "default")),
        secret_name=str(spec_any.get("secretName", "")),
        secret_key=str(spec_any.get("secretKey", "")),
        secret_value=vals,
    )


def _parse_helm_config(helm_raw: Any) -> AppHelmConfig | None:  # noqa: ANN401
    if not isinstance(helm_raw, dict):
        return None
    release = str(helm_raw.get("releaseName")) if helm_raw.get("releaseName") else None
    values = [str(v) for v in (helm_raw.get("valueFiles") or [])]
    return AppHelmConfig(release_name=release, value_files=values)


def _parse_secret_values(seq: Any) -> list[SecretValueSpec]:  # noqa: ANN401
    if not isinstance(seq, list):
        return []
    result: list[SecretValueSpec] = []
    for v in seq:
        if not isinstance(v, dict):
            continue
        spec = _parse_single_secret_value(v)
        if spec is not None:
            result.append(spec)
    return result


def _validate_positive_int(value: Any, field_name: str) -> int:  # noqa: ANN401
    """Validate that a value is a positive integer."""
    if not isinstance(value, int) or value <= 0:
        msg = f"{field_name} must be a positive integer"
        raise ManifestValidationError(msg)
    return value


def _parse_single_secret_value(v: dict[str, Any]) -> SecretValueSpec | None:
    """Parse a single secret value specification."""
    if "fromEnv" in v:
        return SecretValueFromEnv(from_env=str(v["fromEnv"]))
    if "randomBase64" in v:
        num_bytes = _validate_positive_int(v["randomBase64"], "randomBase64")
        return SecretValueRandomBase64(num_bytes=num_bytes)
    if "randomHex" in v:
        num_bytes = _validate_positive_int(v["randomHex"], "randomHex")
        return SecretValueRandomHex(num_bytes=num_bytes)
    if "staticValue" in v:
        return SecretValueStatic(value=str(v["staticValue"]))
    if "sameAs" in v:
        return _parse_same_as_value(v["sameAs"])
    return None


def _parse_same_as_value(same_as_raw: Any) -> SecretValueSameAs:  # noqa: ANN401
    """Parse a sameAs secret value specification."""
    if not isinstance(same_as_raw, dict):
        msg = "sameAs must be a mapping with namespace, secretName, and secretKey"
        raise ManifestValidationError(msg)
    namespace = same_as_raw.get("namespace")
    secret_name = same_as_raw.get("secretName")
    secret_key = same_as_raw.get("secretKey")
    if not all([namespace, secret_name, secret_key]):
        msg = "sameAs requires namespace, secretName, and secretKey fields"
        raise ManifestValidationError(msg)
    return SecretValueSameAs(
        namespace=str(namespace),
        secret_name=str(secret_name),
        secret_key=str(secret_key),
    )


def _parse_coredns_enabled(coredns_raw: dict[str, Any]) -> bool:
    """Parse the enabled flag from CoreDNS config."""
    enabled = coredns_raw.get("enabled", True)
    return enabled if isinstance(enabled, bool) else True


def _parse_coredns_domains(coredns_raw: dict[str, Any]) -> list[str]:
    """Parse the domains list from CoreDNS config."""
    domains_raw = coredns_raw.get("domains")
    if not isinstance(domains_raw, list):
        return ["localtest.me"]
    domains = [str(d) for d in domains_raw if isinstance(d, str)]
    return domains if domains else ["localtest.me"]


def _parse_coredns_rewrite(coredns_raw: Any) -> CoreDnsRewriteConfig:  # noqa: ANN401
    """Parse the CoreDNS rewrite configuration section."""
    if not isinstance(coredns_raw, dict):
        return CoreDnsRewriteConfig()

    return CoreDnsRewriteConfig(
        enabled=_parse_coredns_enabled(coredns_raw),
        domains=_parse_coredns_domains(coredns_raw),
    )


def _parse_ingress(ingress_raw: Any) -> IngressConfig:  # noqa: ANN401
    """Parse the ingress configuration section."""
    if not isinstance(ingress_raw, dict):
        # Return default config if no ingress section or invalid
        return IngressConfig()

    coredns_rewrite = _parse_coredns_rewrite(ingress_raw.get("coreDnsRewrite"))

    return IngressConfig(
        namespace=str(ingress_raw.get("namespace", "ingress-nginx")),
        secret_name=str(ingress_raw.get("secretName", "localargo-ca-cert")),
        secret_key=str(ingress_raw.get("secretKey", "crt")),
        coredns_rewrite=coredns_rewrite,
    )


def _coerce_single_key_mapping(item: Any, ctx: str) -> tuple[str, dict[str, Any]]:  # noqa: ANN401
    if not isinstance(item, dict) or len(item) != 1:
        msg = f"{ctx} must be a single-key mapping of name to spec"
        raise ManifestValidationError(msg)
    name, spec_any = next(iter(item.items()))
    if not isinstance(spec_any, dict):
        msg = f"{ctx}.{name} spec must be a mapping"
        raise ManifestValidationError(msg)
    return str(name), spec_any
