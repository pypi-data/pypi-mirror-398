# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Tests for state checker functions."""

from subprocess import CalledProcessError
from typing import Any
from unittest.mock import MagicMock, Mock, patch

from localargo.config.manifest import (
    ClusterConfig,
    IngressConfig,
    RepoCredEntry,
    SecretEntry,
    SecretValueFromEnv,
    UpManifest,
)
from localargo.core.catalog import AppSpec, AppState
from localargo.core.checkers import (
    check_apps,
    check_argocd,
    check_ca,
    check_cert_manager,
    check_cluster,
    check_nginx_ingress,
    check_repo_creds,
    check_secrets,
)

# =============================================================================
# Test manifest factory for DRY test setup
# =============================================================================


def create_test_manifest(
    *,
    apps: list | None = None,
    repo_creds: list | None = None,
    secrets: list | None = None,
    ingress: IngressConfig | None = None,
) -> UpManifest:
    """Create a test manifest with sensible defaults."""
    return UpManifest(
        clusters=[ClusterConfig(name="test-cluster", provider="kind")],
        apps=apps or [],
        repo_creds=repo_creds or [],
        secrets=secrets or [],
        ingress=ingress or IngressConfig(),
    )


# =============================================================================
# Cluster checker tests
# =============================================================================


class TestClusterChecker:
    """Test cases for cluster state checking."""

    def test_check_cluster_exists_and_ready(self) -> None:
        """Test cluster checker when cluster exists and is ready."""
        with patch("localargo.core.cluster.cluster_manager.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.get_cluster_status.return_value = {
                "exists": True,
                "ready": True,
                "context": "kind-test-cluster",
            }
            mock_get_provider.return_value = mock_provider

            manifest = create_test_manifest()
            status = check_cluster(manifest)

            assert status.state == "completed"
            assert "exists and is ready" in status.reason
            assert status.details["exists"] is True
            assert status.details["ready"] is True

    def test_check_cluster_exists_not_ready(self) -> None:
        """Test cluster checker when cluster exists but is not ready."""
        with patch("localargo.core.cluster.cluster_manager.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.get_cluster_status.return_value = {
                "exists": True,
                "ready": False,
                "context": "kind-test-cluster",
            }
            mock_get_provider.return_value = mock_provider

            manifest = create_test_manifest()
            status = check_cluster(manifest)

            assert status.state == "pending"
            assert "exists but is not ready" in status.reason

    def test_check_cluster_not_exists(self) -> None:
        """Test cluster checker when cluster doesn't exist."""
        with patch("localargo.core.cluster.cluster_manager.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.get_cluster_status.return_value = {
                "exists": False,
                "ready": False,
            }
            mock_get_provider.return_value = mock_provider

            manifest = create_test_manifest()
            status = check_cluster(manifest)

            assert status.state == "pending"
            assert "does not exist" in status.reason

    def test_check_cluster_error_handling(self) -> None:
        """Test cluster checker error handling."""
        with patch("localargo.core.cluster.cluster_manager.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.get_cluster_status.side_effect = Exception("Connection failed")
            mock_get_provider.return_value = mock_provider

            manifest = create_test_manifest()
            status = check_cluster(manifest)

            assert status.state == "pending"
            assert "Unable to determine cluster status" in status.reason


# =============================================================================
# ArgoCD checker tests
# =============================================================================


class TestArgoCDChecker:
    """Test cases for ArgoCD state checking."""

    def test_check_argocd_installed_and_ready(self) -> None:
        """Test ArgoCD checker when installed and ready."""
        with patch("localargo.core.checkers.run_subprocess") as mock_run:
            # First call: check deployment exists
            mock_exists = Mock()
            mock_exists.returncode = 0
            mock_exists.stdout = "argocd-server"

            # Second call: get ready replicas
            mock_ready = Mock()
            mock_ready.returncode = 0
            mock_ready.stdout = "1"

            mock_run.side_effect = [mock_exists, mock_ready]

            manifest = create_test_manifest()
            status = check_argocd(manifest)

            assert status.state == "completed"
            assert "ArgoCD is installed and ready" in status.reason
            assert status.details["ready_replicas"] == 1

    def test_check_argocd_deployment_exists_not_ready(self) -> None:
        """Test ArgoCD checker when deployment exists but not ready."""
        with patch("localargo.core.checkers.run_subprocess") as mock_run:
            # First call: check deployment exists
            mock_exists = Mock()
            mock_exists.returncode = 0
            mock_exists.stdout = "argocd-server"

            # Second call: get ready replicas (0)
            mock_not_ready = Mock()
            mock_not_ready.returncode = 0
            mock_not_ready.stdout = "0"

            mock_run.side_effect = [mock_exists, mock_not_ready]

            manifest = create_test_manifest()
            status = check_argocd(manifest)

            assert status.state == "pending"
            assert "exists but is not ready" in status.reason

    def test_check_argocd_not_installed(self) -> None:
        """Test ArgoCD checker when not installed."""
        with patch("localargo.core.checkers.run_subprocess") as mock_run:
            # Return empty stdout to indicate deployment not found
            mock_not_found = Mock()
            mock_not_found.returncode = 0
            mock_not_found.stdout = ""  # Empty = not found

            mock_run.return_value = mock_not_found

            manifest = create_test_manifest()
            status = check_argocd(manifest)

            assert status.state == "pending"
            assert "ArgoCD server deployment not found" in status.reason

    def test_check_argocd_error_handling(self) -> None:
        """Test ArgoCD checker error handling."""
        with patch("localargo.core.checkers.run_subprocess") as mock_run:
            mock_run.side_effect = RuntimeError("kubectl failed")

            manifest = create_test_manifest()
            status = check_argocd(manifest)

            assert status.state == "pending"
            assert "Unable to determine ArgoCD status" in status.reason


# =============================================================================
# Nginx ingress checker tests
# =============================================================================


class TestNginxIngressChecker:
    """Test cases for nginx ingress state checking."""

    def test_check_nginx_installed_and_ready(self) -> None:
        """Test nginx checker when installed and ready."""
        with patch("localargo.core.checkers.run_subprocess") as mock_run:
            # First call: check deployment exists
            mock_exists = Mock()
            mock_exists.returncode = 0
            mock_exists.stdout = "ingress-nginx-controller"

            # Second call: get ready replicas
            mock_ready = Mock()
            mock_ready.returncode = 0
            mock_ready.stdout = "2"

            mock_run.side_effect = [mock_exists, mock_ready]

            manifest = create_test_manifest()
            status = check_nginx_ingress(manifest)

            assert status.state == "completed"
            assert "is installed and ready" in status.reason
            assert status.details["ready_replicas"] == 2  # noqa: PLR2004

    def test_check_nginx_not_installed(self) -> None:
        """Test nginx checker when not installed."""
        with patch("localargo.core.checkers.run_subprocess") as mock_run:
            # Return empty stdout to indicate deployment not found
            mock_not_found = Mock()
            mock_not_found.returncode = 0
            mock_not_found.stdout = ""  # Empty = not found

            mock_run.return_value = mock_not_found

            manifest = create_test_manifest()
            status = check_nginx_ingress(manifest)

            assert status.state == "pending"
            assert "not found" in status.reason


# =============================================================================
# Secrets checker tests
# =============================================================================


class TestSecretsChecker:
    """Test cases for secrets state checking."""

    def test_check_secrets_no_secrets(self) -> None:
        """Test secrets checker when no secrets are defined."""
        manifest = create_test_manifest()
        status = check_secrets(manifest)

        assert status.state == "completed"
        assert "No secrets to check" in status.reason

    def test_check_secrets_all_exist(self, mock_subprocess_run: MagicMock) -> None:
        """Test secrets checker when all secrets exist."""
        mock_exists = Mock()
        mock_exists.returncode = 0
        mock_exists.stdout = "my-secret"
        mock_subprocess_run.return_value = mock_exists

        manifest = create_test_manifest(
            secrets=[
                SecretEntry(
                    name="test-secret",
                    namespace="default",
                    secret_name="my-secret",
                    secret_key="password",
                    secret_value=[SecretValueFromEnv(from_env="TEST_PASSWORD")],
                ),
            ],
        )

        status = check_secrets(manifest)

        assert status.state == "completed"
        assert "All 1 secrets exist" in status.reason
        assert len(status.details["existing_secrets"]) == 1

    def test_check_secrets_some_missing(self) -> None:
        """Test secrets checker when some secrets are missing."""
        call_count = 0

        def mock_run(cmd: list[str], **_kwargs: Any) -> Mock:  # noqa: ANN401
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                result = Mock()
                result.returncode = 0
                result.stdout = "secret1"
                return result
            raise CalledProcessError(1, cmd)

        with patch("localargo.core.checkers.run_subprocess", side_effect=mock_run):
            manifest = create_test_manifest(
                secrets=[
                    SecretEntry(
                        name="secret1",
                        namespace="default",
                        secret_name="secret1",
                        secret_key="key1",
                        secret_value=[SecretValueFromEnv(from_env="VAR1")],
                    ),
                    SecretEntry(
                        name="secret2",
                        namespace="test-ns",
                        secret_name="secret2",
                        secret_key="key2",
                        secret_value=[SecretValueFromEnv(from_env="VAR2")],
                    ),
                ],
            )

            status = check_secrets(manifest)

            assert status.state == "pending"
            assert "1 of 2 secrets missing" in status.reason
            assert len(status.details["missing_secrets"]) == 1
            assert len(status.details["existing_secrets"]) == 1


# =============================================================================
# Repo credentials checker tests
# =============================================================================


class TestRepoCredsChecker:
    """Test cases for repo credentials state checking."""

    def test_check_repo_creds_no_creds(self) -> None:
        """Test repo creds checker when no credentials are defined."""
        manifest = create_test_manifest()
        status = check_repo_creds(manifest)

        assert status.state == "completed"
        assert "No repo credentials to check" in status.reason

    def test_check_repo_creds_no_client(self) -> None:
        """Test repo creds checker when no ArgoCD client provided."""
        manifest = create_test_manifest(
            repo_creds=[
                RepoCredEntry(
                    name="test-repo",
                    repo_url="https://github.com/test/repo",
                    username="test",
                    password="secret",
                ),
            ],
        )

        status = check_repo_creds(manifest, client=None)

        assert status.state == "pending"
        assert "ArgoCD client required" in status.reason

    def test_check_repo_creds_all_configured(self) -> None:
        """Test repo creds checker when all are configured."""
        with patch("localargo.core.checkers.run_json") as mock_run_json:
            mock_run_json.return_value = [
                {"repo": "https://github.com/test/repo", "username": "test"},
            ]

            mock_client = Mock()
            manifest = create_test_manifest(
                repo_creds=[
                    RepoCredEntry(
                        name="test-repo",
                        repo_url="https://github.com/test/repo",
                        username="test",
                        password="secret",
                    ),
                ],
            )

            status = check_repo_creds(manifest, client=mock_client)

            assert status.state == "completed"
            assert "All 1 repo credentials configured" in status.reason

    def test_check_repo_creds_some_missing(self) -> None:
        """Test repo creds checker when some are missing."""
        with patch("localargo.core.checkers.run_json") as mock_run_json:
            mock_run_json.return_value = []

            mock_client = Mock()
            manifest = create_test_manifest(
                repo_creds=[
                    RepoCredEntry(
                        name="test-repo",
                        repo_url="https://github.com/test/repo",
                        username="test",
                        password="secret",
                    ),
                ],
            )

            status = check_repo_creds(manifest, client=mock_client)

            assert status.state == "pending"
            assert "1 of 1 repo credentials missing" in status.reason


# =============================================================================
# Applications checker tests
# =============================================================================


class TestAppsChecker:
    """Test cases for applications state checking."""

    def test_check_apps_no_apps(self) -> None:
        """Test apps checker when no applications are defined."""
        manifest = create_test_manifest()
        status = check_apps(manifest)

        assert status.state == "completed"
        assert "No applications to check" in status.reason

    def test_check_apps_no_client(self) -> None:
        """Test apps checker when no ArgoCD client provided."""
        manifest = create_test_manifest(
            apps=[
                AppSpec(
                    name="test-app",
                    repo="https://github.com/test/repo",
                    namespace="default",
                ),
            ],
        )

        status = check_apps(manifest, client=None)

        assert status.state == "pending"
        assert "ArgoCD client required" in status.reason

    def test_check_apps_all_synced(self) -> None:
        """Test apps checker when all apps are synced and healthy."""
        mock_client = Mock()
        mock_client.get_apps.return_value = [
            AppState(
                name="test-app",
                namespace="default",
                health="Healthy",
                sync="Synced",
            ),
        ]

        manifest = create_test_manifest(
            apps=[
                AppSpec(
                    name="test-app",
                    repo="https://github.com/test/repo",
                    namespace="default",
                ),
            ],
        )

        status = check_apps(manifest, client=mock_client)

        assert status.state == "completed"
        assert "All 1 applications are synced and healthy" in status.reason

    def test_check_apps_some_missing(self) -> None:
        """Test apps checker when some apps are not deployed."""
        mock_client = Mock()
        mock_client.get_apps.return_value = []

        manifest = create_test_manifest(
            apps=[
                AppSpec(
                    name="test-app",
                    repo="https://github.com/test/repo",
                    namespace="default",
                ),
            ],
        )

        status = check_apps(manifest, client=mock_client)

        assert status.state == "pending"
        assert "1 of 1 applications not deployed" in status.reason

    def test_check_apps_some_unsynced(self) -> None:
        """Test apps checker when some apps are deployed but not synced."""
        mock_client = Mock()
        mock_client.get_apps.return_value = [
            AppState(
                name="test-app",
                namespace="default",
                health="Progressing",
                sync="OutOfSync",
            ),
        ]

        manifest = create_test_manifest(
            apps=[
                AppSpec(
                    name="test-app",
                    repo="https://github.com/test/repo",
                    namespace="default",
                ),
            ],
        )

        status = check_apps(manifest, client=mock_client)

        assert status.state == "pending"
        assert "1 of 1 applications need sync" in status.reason


# =============================================================================
# Cert-manager checker tests
# =============================================================================


class TestCertManagerChecker:
    """Test cases for cert-manager state checking."""

    def test_check_cert_manager_installed_and_ready(self) -> None:
        """Test cert-manager checker when installed and ready."""
        with patch("localargo.core.checkers.run_subprocess") as mock_run:
            mock_result = Mock()
            mock_result.stdout = "True"
            mock_run.return_value = mock_result

            manifest = create_test_manifest()
            status = check_cert_manager(manifest)

            assert status.state == "completed"
            assert "cert-manager is installed and ready" in status.reason
            assert status.details["cert_manager_ready"] is True

    def test_check_cert_manager_deployment_exists_not_ready(self) -> None:
        """Test cert-manager checker when deployment exists but not ready."""
        with patch("localargo.core.checkers.run_subprocess") as mock_run:
            mock_result = Mock()
            mock_result.stdout = "False"
            mock_run.return_value = mock_result

            manifest = create_test_manifest()
            status = check_cert_manager(manifest)

            assert status.state == "pending"
            assert "not installed or not ready" in status.reason

    def test_check_cert_manager_not_installed(self) -> None:
        """Test cert-manager checker when not installed."""
        with patch("localargo.core.checkers.run_subprocess") as mock_run:
            mock_run.side_effect = CalledProcessError(1, "kubectl")

            manifest = create_test_manifest()
            status = check_cert_manager(manifest)

            assert status.state == "pending"
            assert "not installed or not ready" in status.reason

    def test_check_cert_manager_error_handling(self) -> None:
        """Test cert-manager checker error handling."""
        with patch("localargo.core.checkers.run_subprocess") as mock_run_subprocess:
            mock_run_subprocess.side_effect = RuntimeError("kubectl failed")

            manifest = create_test_manifest()
            status = check_cert_manager(manifest)

            assert status.state == "pending"
            assert "Failed to check cert-manager status" in status.reason


# =============================================================================
# CA checker tests
# =============================================================================


class TestCAChecker:
    """Test cases for CA state checking."""

    def test_check_ca_fully_set_up(self) -> None:
        """Test CA checker when all components are properly set up."""
        with (
            patch("localargo.core.checkers._check_cluster_issuer_exists") as mock_issuer,
            patch("localargo.core.checkers._check_certificate_ready") as mock_cert,
            patch("localargo.core.checkers._check_secret_exists") as mock_secret,
        ):
            mock_issuer.return_value = True
            mock_cert.return_value = True
            mock_secret.return_value = True

            manifest = create_test_manifest(
                ingress=IngressConfig(namespace="test-ns", secret_name="ca", secret_key="crt"),
            )

            status = check_ca(manifest)

            assert status.state == "completed"
            assert "CA setup is complete" in status.reason
            assert status.details["selfsigned_issuer_exists"] is True
            assert status.details["root_ca_ready"] is True
            assert status.details["ca_issuer_exists"] is True
            assert status.details["wildcard_cert_ready"] is True
            assert status.details["user_secret_exists"] is True

    def test_check_ca_missing_components(self) -> None:
        """Test CA checker when some components are missing."""
        with (
            patch("localargo.core.checkers._check_cluster_issuer_exists") as mock_issuer,
            patch("localargo.core.checkers._check_certificate_ready") as mock_cert,
            patch("localargo.core.checkers._check_secret_exists") as mock_secret,
        ):
            mock_issuer.return_value = True
            mock_cert.side_effect = [True, False]
            mock_secret.return_value = False

            manifest = create_test_manifest(
                ingress=IngressConfig(namespace="test-ns", secret_name="ca", secret_key="crt"),
            )

            status = check_ca(manifest)

            assert status.state == "pending"
            assert "CA setup incomplete" in status.reason

    def test_check_ca_error_handling(self) -> None:
        """Test CA checker error handling."""
        with patch("localargo.core.checkers._check_cluster_issuer_exists") as mock_issuer:
            mock_issuer.side_effect = RuntimeError("kubectl failed")

            manifest = create_test_manifest()
            status = check_ca(manifest)

            assert status.state == "pending"
            assert "Failed to check CA status" in status.reason
