# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Tests for CA certificate distribution to app namespaces."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from localargo.config.manifest import AppEntry, IngressConfig, UpManifest
from localargo.core.ca import (
    check_ca_secret_in_namespace,
    distribute_ca_to_app_namespaces,
    distribute_ca_to_namespace,
    get_app_namespaces_needing_ca,
)
from localargo.core.checkers import check_ca_distribution
from localargo.core.executors import execute_ca_distribution


class TestGetAppNamespacesNeedingCA:
    """Tests for get_app_namespaces_needing_ca function."""

    def test_filters_out_ingress_namespace(self) -> None:
        """Should filter out the ingress namespace."""
        app_namespaces = ["core", "ingress-nginx", "keycloak", "bookstack"]
        result = get_app_namespaces_needing_ca(app_namespaces, "ingress-nginx")
        assert result == ["core", "keycloak", "bookstack"]

    def test_removes_duplicates_preserving_order(self) -> None:
        """Should remove duplicate namespaces while preserving order."""
        app_namespaces = ["core", "keycloak", "core", "bookstack", "keycloak"]
        result = get_app_namespaces_needing_ca(app_namespaces, "ingress-nginx")
        assert result == ["core", "keycloak", "bookstack"]

    def test_filters_empty_namespaces(self) -> None:
        """Should filter out empty namespace strings."""
        app_namespaces = ["core", "", "keycloak", ""]
        result = get_app_namespaces_needing_ca(app_namespaces, "ingress-nginx")
        assert result == ["core", "keycloak"]

    def test_empty_list_returns_empty(self) -> None:
        """Should return empty list when no app namespaces."""
        result = get_app_namespaces_needing_ca([], "ingress-nginx")
        assert result == []

    def test_all_namespaces_are_ingress_namespace(self) -> None:
        """Should return empty list when all namespaces are ingress namespace."""
        app_namespaces = ["ingress-nginx", "ingress-nginx"]
        result = get_app_namespaces_needing_ca(app_namespaces, "ingress-nginx")
        assert result == []


class TestCheckCASecretInNamespace:
    """Tests for check_ca_secret_in_namespace function."""

    @patch("localargo.core.ca.resource_exists")
    def test_returns_true_when_secret_exists(self, mock_resource_exists: MagicMock) -> None:
        """Should return True when secret exists."""
        mock_resource_exists.return_value = True
        result = check_ca_secret_in_namespace("core", "localargo-ca-cert")
        assert result is True
        mock_resource_exists.assert_called_once_with("secret", "localargo-ca-cert", namespace="core")

    @patch("localargo.core.ca.resource_exists")
    def test_returns_false_when_secret_missing(self, mock_resource_exists: MagicMock) -> None:
        """Should return False when secret doesn't exist."""
        mock_resource_exists.return_value = False
        result = check_ca_secret_in_namespace("core", "localargo-ca-cert")
        assert result is False


class TestDistributeCAToNamespace:
    """Tests for distribute_ca_to_namespace function."""

    @patch("localargo.core.ca.apply_yaml")
    @patch("localargo.core.ca.run_kubectl")
    @patch("localargo.core.ca.ensure_namespace")
    def test_distributes_ca_successfully(
        self,
        mock_ensure_namespace: MagicMock,
        mock_run_kubectl: MagicMock,
        mock_apply_yaml: MagicMock,
    ) -> None:
        """Should distribute CA secret to namespace."""
        mock_run_kubectl.return_value = MagicMock(stdout="base64encodedcert")
        ingress_config = IngressConfig(
            namespace="ingress-nginx",
            secret_name="localargo-ca-cert",
            secret_key="crt",
        )

        distribute_ca_to_namespace("core", ingress_config)

        mock_ensure_namespace.assert_called_once_with("core")
        mock_run_kubectl.assert_called_once()
        mock_apply_yaml.assert_called_once()
        # Verify the YAML contains expected values
        yaml_content = mock_apply_yaml.call_args[0][0]
        assert "namespace: core" in yaml_content
        assert "name: localargo-ca-cert" in yaml_content
        assert "localargo.dev/ca-distribution" in yaml_content

    @patch("localargo.core.ca.ensure_namespace")
    @patch("localargo.core.ca.run_kubectl")
    def test_raises_when_ca_cert_not_found(
        self,
        mock_run_kubectl: MagicMock,
        mock_ensure_namespace: MagicMock,
    ) -> None:
        """Should raise RuntimeError when CA cert not found."""
        mock_run_kubectl.return_value = MagicMock(stdout="")
        ingress_config = IngressConfig()

        with pytest.raises(RuntimeError, match="Failed to retrieve CA certificate"):
            distribute_ca_to_namespace("core", ingress_config)

        # Verify namespace was ensured before attempting to get cert
        mock_ensure_namespace.assert_called_once_with("core")


class TestDistributeCAToAppNamespaces:
    """Tests for distribute_ca_to_app_namespaces function."""

    @patch("localargo.core.ca.distribute_ca_to_namespace")
    @patch("localargo.core.ca.check_ca_secret_in_namespace")
    def test_distributes_to_all_namespaces(
        self,
        mock_check: MagicMock,
        mock_distribute: MagicMock,
    ) -> None:
        """Should distribute CA to all namespaces that need it."""
        mock_check.return_value = False
        ingress_config = IngressConfig(namespace="ingress-nginx")
        app_namespaces = ["core", "keycloak", "bookstack"]

        results = distribute_ca_to_app_namespaces(app_namespaces, ingress_config)

        assert len(results) == 3  # noqa: PLR2004
        assert all(results.values())
        assert mock_distribute.call_count == 3  # noqa: PLR2004

    @patch("localargo.core.ca.distribute_ca_to_namespace")
    @patch("localargo.core.ca.check_ca_secret_in_namespace")
    def test_skips_namespaces_with_existing_secret(
        self,
        mock_check: MagicMock,
        mock_distribute: MagicMock,
    ) -> None:
        """Should skip namespaces that already have the CA secret."""
        mock_check.side_effect = [True, False, True]  # core exists, keycloak doesn't, bookstack exists
        ingress_config = IngressConfig(namespace="ingress-nginx")
        app_namespaces = ["core", "keycloak", "bookstack"]

        results = distribute_ca_to_app_namespaces(app_namespaces, ingress_config)

        assert len(results) == 3  # noqa: PLR2004
        assert all(results.values())
        # Only keycloak should have triggered distribute
        mock_distribute.assert_called_once()

    @patch("localargo.core.ca.check_ca_secret_in_namespace")
    def test_returns_empty_when_no_namespaces_need_ca(
        self,
        mock_check: MagicMock,
    ) -> None:
        """Should return empty dict when no namespaces need CA."""
        ingress_config = IngressConfig(namespace="ingress-nginx")
        app_namespaces = ["ingress-nginx"]  # Only the ingress namespace

        results = distribute_ca_to_app_namespaces(app_namespaces, ingress_config)

        assert results == {}
        mock_check.assert_not_called()


class TestCheckCADistribution:
    """Tests for check_ca_distribution checker function."""

    def _create_manifest(self, app_namespaces: list[str]) -> UpManifest:
        """Create a test manifest with given app namespaces."""
        apps = [AppEntry(name=f"app-{i}", namespace=ns, app_file=None) for i, ns in enumerate(app_namespaces)]
        return UpManifest(
            clusters=[],
            apps=apps,
            repo_creds=[],
            secrets=[],
            ingress=IngressConfig(namespace="ingress-nginx", secret_name="localargo-ca-cert"),
        )

    def test_completed_when_no_app_namespaces(self) -> None:
        """Should return completed when no apps defined."""
        manifest = self._create_manifest([])
        status = check_ca_distribution(manifest)
        assert status.state == "completed"
        assert "No app namespaces" in status.reason

    def test_completed_when_all_namespaces_are_ingress(self) -> None:
        """Should return completed when all apps are in ingress namespace."""
        manifest = self._create_manifest(["ingress-nginx", "ingress-nginx"])
        status = check_ca_distribution(manifest)
        assert status.state == "completed"

    @patch("localargo.core.checkers.check_ca_secret_in_namespace")
    def test_completed_when_all_namespaces_have_ca(
        self,
        mock_check: MagicMock,
    ) -> None:
        """Should return completed when all namespaces have CA secret."""
        mock_check.return_value = True
        manifest = self._create_manifest(["core", "keycloak", "bookstack"])

        status = check_ca_distribution(manifest)

        assert status.state == "completed"
        assert "3 app namespaces" in status.reason

    @patch("localargo.core.checkers.check_ca_secret_in_namespace")
    def test_pending_when_some_namespaces_missing_ca(
        self,
        mock_check: MagicMock,
    ) -> None:
        """Should return pending when some namespaces are missing CA secret."""
        mock_check.side_effect = [True, False, True]  # core has, keycloak missing, bookstack has
        manifest = self._create_manifest(["core", "keycloak", "bookstack"])

        status = check_ca_distribution(manifest)

        assert status.state == "pending"
        assert "1 of 3" in status.reason
        assert status.details is not None
        assert "keycloak" in status.details["namespaces_without_ca"]


class TestExecuteCADistribution:
    """Tests for execute_ca_distribution executor function."""

    def _create_manifest(self, app_namespaces: list[str]) -> UpManifest:
        """Create a test manifest with given app namespaces."""
        apps = [AppEntry(name=f"app-{i}", namespace=ns, app_file=None) for i, ns in enumerate(app_namespaces)]
        return UpManifest(
            clusters=[],
            apps=apps,
            repo_creds=[],
            secrets=[],
            ingress=IngressConfig(namespace="ingress-nginx"),
        )

    @patch("localargo.core.executors.distribute_ca_to_app_namespaces")
    def test_executes_distribution(self, mock_distribute: MagicMock) -> None:
        """Should call distribute_ca_to_app_namespaces."""
        mock_distribute.return_value = {"core": True, "keycloak": True}
        manifest = self._create_manifest(["core", "keycloak"])

        execute_ca_distribution(manifest)

        mock_distribute.assert_called_once()
        call_args = mock_distribute.call_args
        assert call_args[0][0] == ["core", "keycloak"]

    @patch("localargo.core.executors.distribute_ca_to_app_namespaces")
    def test_skips_when_no_app_namespaces(self, mock_distribute: MagicMock) -> None:
        """Should skip when no app namespaces."""
        manifest = self._create_manifest([])

        execute_ca_distribution(manifest)

        mock_distribute.assert_not_called()
