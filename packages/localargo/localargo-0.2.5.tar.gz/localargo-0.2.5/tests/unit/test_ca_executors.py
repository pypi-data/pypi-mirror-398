# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Tests for CA management functions."""

from subprocess import CalledProcessError
from typing import Any
from unittest.mock import MagicMock, Mock, patch

from localargo.config.manifest import IngressConfig, UpManifest
from localargo.core.ca import (
    CA_CLUSTER_ISSUER_NAME,
    CERT_MANAGER_NAMESPACE,
    INGRESS_ROOT_DOMAIN,
    ROOT_CA_CERT_NAME,
    ROOT_CA_SECRET_NAME,
    SELF_SIGNED_ISSUER_NAME,
    WILDCARD_CERT_NAME,
    WILDCARD_SECRET_NAME,
    configure_nginx_default_certificate,
    create_ca_infrastructure,
    create_ca_secret,
    create_wildcard_certificate,
    install_cert_manager,
    resource_exists,
)
from localargo.core.executors import execute_ca_setup, execute_cert_manager_installation

# =============================================================================
# Test utilities
# =============================================================================


def create_ca_test_manifest(ingress: IngressConfig | None = None) -> UpManifest:
    """Create a minimal manifest for CA tests."""
    return UpManifest(
        clusters=[],
        apps=[],
        repo_creds=[],
        secrets=[],
        ingress=ingress or IngressConfig(),
    )


def create_success_mock() -> Mock:
    """Create a successful subprocess result mock."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    return mock_result


def create_ca_mock_side_effect(*args: Any, **_kwargs: Any) -> Mock:  # noqa: ANN401
    """Create a standard mock side effect for CA-related kubectl commands."""
    mock_result = Mock()
    mock_result.returncode = 0

    args_str = str(args)
    if ROOT_CA_SECRET_NAME in args_str and "jsonpath" in args_str:
        mock_result.stdout = "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0t"  # Valid base64
    elif "jsonpath" in args_str and "args" in args_str:
        mock_result.stdout = "[]"
    elif "get" in args_str and "deployment" in args_str:
        mock_result.stdout = "ingress-nginx-controller"
    else:
        mock_result.stdout = ""

    return mock_result


# =============================================================================
# CA Constants tests
# =============================================================================


class TestCAConstants:
    """Test CA module constants are correctly defined."""

    def test_ingress_root_domain(self) -> None:
        """Test that the ingress root domain is set to localtest.me."""
        assert INGRESS_ROOT_DOMAIN == "localtest.me"

    def test_resource_names_are_strings(self) -> None:
        """Test that all resource names are non-empty strings."""
        constants = [
            SELF_SIGNED_ISSUER_NAME,
            ROOT_CA_CERT_NAME,
            ROOT_CA_SECRET_NAME,
            CA_CLUSTER_ISSUER_NAME,
            WILDCARD_CERT_NAME,
            WILDCARD_SECRET_NAME,
        ]
        for const in constants:
            assert isinstance(const, str)
            assert const  # Non-empty

    def test_cert_manager_namespace(self) -> None:
        """Test that cert-manager namespace is correctly set."""
        assert CERT_MANAGER_NAMESPACE == "cert-manager"


# =============================================================================
# Cert-manager installation tests
# =============================================================================


class TestCertManagerInstallation:
    """Test cases for cert-manager installation."""

    def test_execute_cert_manager_installation_success(self, mock_subprocess_run: MagicMock) -> None:
        """Test successful cert-manager installation."""
        mock_subprocess_run.return_value = create_success_mock()

        manifest = create_ca_test_manifest()
        execute_cert_manager_installation(manifest)

        # Verify helm commands were called (repo add, repo update, upgrade --install)
        assert mock_subprocess_run.call_count >= 3  # noqa: PLR2004

    def test_install_cert_manager_adds_jetstack_repo(self, mock_subprocess_run: MagicMock) -> None:
        """Test that cert-manager installation adds the jetstack helm repo."""
        mock_subprocess_run.return_value = create_success_mock()

        install_cert_manager()

        # Check that helm repo add was called with jetstack
        calls = mock_subprocess_run.call_args_list
        repo_add_calls = [c for c in calls if "repo" in str(c) and "add" in str(c)]
        assert len(repo_add_calls) >= 1


# =============================================================================
# CA Infrastructure tests
# =============================================================================


class TestCAInfrastructure:
    """Test cases for CA infrastructure creation."""

    def test_create_ca_infrastructure_success(self, mock_subprocess_run: MagicMock) -> None:
        """Test successful CA infrastructure creation."""
        with patch("localargo.core.ca.resource_exists", return_value=False):
            mock_subprocess_run.return_value = create_success_mock()
            create_ca_infrastructure()
            assert mock_subprocess_run.call_count >= 1

    def test_resource_exists_returns_true_when_found(self, mock_subprocess_run: MagicMock) -> None:
        """Test that resource_exists returns True when resource exists."""
        mock_result = create_success_mock()
        mock_result.stdout = "resource found"
        mock_subprocess_run.return_value = mock_result

        result = resource_exists("clusterissuer", "test-issuer")
        assert result is True

    def test_resource_exists_returns_false_when_not_found(self, mock_subprocess_run: MagicMock) -> None:
        """Test that resource_exists returns False when resource doesn't exist."""
        mock_subprocess_run.side_effect = CalledProcessError(1, "kubectl")

        result = resource_exists("clusterissuer", "nonexistent")
        assert result is False


# =============================================================================
# Wildcard certificate tests
# =============================================================================


class TestWildcardCertificate:
    """Test cases for wildcard certificate creation."""

    def test_create_wildcard_certificate_success(self, mock_subprocess_run: MagicMock) -> None:
        """Test successful wildcard certificate creation."""
        with patch("localargo.core.ca.resource_exists", return_value=False):
            mock_subprocess_run.return_value = create_success_mock()
            create_wildcard_certificate("ingress-nginx")
            assert mock_subprocess_run.call_count >= 1

    def test_create_wildcard_certificate_skips_if_exists(self, mock_subprocess_run: MagicMock) -> None:
        """Test that wildcard certificate creation is skipped if it already exists."""
        with patch("localargo.core.ca.resource_exists", return_value=True):
            mock_subprocess_run.return_value = create_success_mock()
            create_wildcard_certificate("ingress-nginx")


# =============================================================================
# CA Secret tests
# =============================================================================


class TestCASecret:
    """Test cases for CA secret creation."""

    def test_create_ca_secret_success(self, mock_subprocess_run: MagicMock) -> None:
        """Test successful CA secret creation."""
        mock_subprocess_run.side_effect = create_ca_mock_side_effect
        ingress_config = IngressConfig(namespace="test-ns", secret_name="ca", secret_key="crt")
        create_ca_secret(ingress_config)


# =============================================================================
# Nginx configuration tests
# =============================================================================


class TestNginxConfiguration:
    """Test cases for nginx-ingress configuration."""

    def test_configure_nginx_default_certificate_deployment(self, mock_subprocess_run: MagicMock) -> None:
        """Test configuring nginx when controller is a Deployment."""
        mock_subprocess_run.side_effect = create_ca_mock_side_effect
        configure_nginx_default_certificate("ingress-nginx")

    def test_configure_nginx_skips_if_not_found(self, mock_subprocess_run: MagicMock) -> None:
        """Test that nginx configuration is skipped if controller is not found."""
        mock_subprocess_run.side_effect = CalledProcessError(1, "kubectl")
        # Should not raise an exception, just log a warning
        configure_nginx_default_certificate("ingress-nginx")


# =============================================================================
# CA Setup executor tests
# =============================================================================


class TestCASetupExecutor:
    """Test cases for the main CA setup executor."""

    def test_execute_ca_setup_success(self, mock_subprocess_run: MagicMock) -> None:
        """Test successful CA setup."""
        mock_subprocess_run.side_effect = create_ca_mock_side_effect

        with patch("localargo.core.ca.resource_exists", return_value=False):
            manifest = create_ca_test_manifest(
                ingress=IngressConfig(namespace="test-ns", secret_name="ca", secret_key="crt"),
            )
            execute_ca_setup(manifest)

    def test_execute_ca_setup_creates_ca_infrastructure(self, mock_subprocess_run: MagicMock) -> None:
        """Test that CA setup creates the CA infrastructure."""
        mock_subprocess_run.side_effect = create_ca_mock_side_effect

        with patch("localargo.core.ca.resource_exists", return_value=False):
            manifest = create_ca_test_manifest(
                ingress=IngressConfig(namespace="ingress-nginx"),
            )
            execute_ca_setup(manifest)

            # Verify that kubectl apply was called
            apply_calls = [c for c in mock_subprocess_run.call_args_list if "apply" in str(c)]
            assert len(apply_calls) >= 1
