# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Tests for ingress configuration functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from localargo.config.manifest import IngressConfig, _parse_ingress, load_up_manifest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# =============================================================================
# IngressConfig dataclass tests
# =============================================================================


class TestIngressConfig:
    """Test cases for IngressConfig dataclass."""

    def test_ingress_config_defaults(self) -> None:
        """Test IngressConfig with default values."""
        config = IngressConfig()

        assert config.namespace == "ingress-nginx"
        assert config.secret_name == "localargo-ca-cert"
        assert config.secret_key == "crt"

    def test_ingress_config_custom_values(self) -> None:
        """Test IngressConfig with custom values."""
        config = IngressConfig(
            namespace="my-ingress",
            secret_name="my-ca-secret",
            secret_key="ca.pem",
        )

        assert config.namespace == "my-ingress"
        assert config.secret_name == "my-ca-secret"
        assert config.secret_key == "ca.pem"


# =============================================================================
# Ingress parsing tests
# =============================================================================


class TestIngressParsing:
    """Test cases for ingress configuration parsing."""

    def test_parse_ingress_none(self) -> None:
        """Test parsing when ingress section is None."""
        result = _parse_ingress(None)
        assert isinstance(result, IngressConfig)

    def test_parse_ingress_empty_dict(self) -> None:
        """Test parsing when ingress section is empty dict."""
        result = _parse_ingress({})
        assert isinstance(result, IngressConfig)

    def test_parse_ingress_full_config(self) -> None:
        """Test parsing complete ingress configuration."""
        ingress_data = {
            "namespace": "custom-ingress",
            "secretName": "company-ca",
            "secretKey": "certificate.pem",
        }

        result = _parse_ingress(ingress_data)

        assert result.namespace == "custom-ingress"
        assert result.secret_name == "company-ca"
        assert result.secret_key == "certificate.pem"

    def test_parse_ingress_partial_config(self) -> None:
        """Test parsing partial ingress configuration (uses defaults)."""
        result = _parse_ingress({})

        assert result.namespace == "ingress-nginx"
        assert result.secret_name == "localargo-ca-cert"
        assert result.secret_key == "crt"


# =============================================================================
# Manifest loading tests
# =============================================================================


class TestManifestLoading:
    """Test cases for loading manifests with ingress configuration."""

    @pytest.fixture
    def create_yaml_file(self, tmp_path: Path) -> Callable[[str], str]:
        """Fixture to create temporary YAML files."""

        def _create(content: str) -> str:
            yaml_file = tmp_path / "localargo.yaml"
            yaml_file.write_text(content)
            return str(yaml_file)

        return _create

    def test_load_manifest_without_ingress(self, create_yaml_file: Callable[[str], str]) -> None:
        """Test loading manifest without ingress section."""
        yaml_content = """
cluster:
  - name: test-cluster
    provider: kind

apps: []
repo_creds: []
secrets: []
"""
        temp_file = create_yaml_file(yaml_content)
        manifest = load_up_manifest(temp_file)

        # Should have default ingress config
        assert manifest.ingress.namespace == "ingress-nginx"
        assert manifest.ingress.secret_name == "localargo-ca-cert"
        assert manifest.ingress.secret_key == "crt"

    def test_load_manifest_with_ingress(self, create_yaml_file: Callable[[str], str]) -> None:
        """Test loading manifest with full ingress configuration."""
        yaml_content = """
cluster:
  - name: test-cluster
    provider: kind

ingress:
  namespace: ingress-system
  secretName: internal-ca
  secretKey: ca.crt

apps: []
repo_creds: []
secrets: []
"""
        temp_file = create_yaml_file(yaml_content)
        manifest = load_up_manifest(temp_file)

        # Should have custom ingress config
        assert manifest.ingress.namespace == "ingress-system"
        assert manifest.ingress.secret_name == "internal-ca"
        assert manifest.ingress.secret_key == "ca.crt"
