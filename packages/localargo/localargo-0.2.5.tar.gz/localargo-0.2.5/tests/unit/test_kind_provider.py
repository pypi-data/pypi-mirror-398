"""Tests for Kind provider functionality."""

# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
from subprocess import CalledProcessError
from unittest.mock import MagicMock, patch

import pytest

from localargo.providers.base import (
    ClusterCreationError,
    ClusterOperationError,
    ProviderNotAvailableError,
)
from localargo.providers.kind import KindProvider
from tests.conftest import assert_command_contains


class TestKindProviderBasics:
    """Basic tests for KindProvider."""

    def test_provider_name(self) -> None:
        """Test that provider_name returns 'kind'."""
        provider = KindProvider(name="test")
        assert provider.provider_name == "kind"

    def test_get_context_name(self) -> None:
        """Test get_context_name returns correct context name format."""
        provider = KindProvider(name="demo")
        assert provider.get_context_name("demo") == "kind-demo"


class TestKindProviderAvailability:
    """Test KindProvider availability checks."""

    def test_is_available_with_kind_present(self) -> None:
        """Test is_available returns True when kind is found and works."""
        provider = KindProvider(name="test")
        assert provider.is_available() is True

    def test_is_available_with_kind_not_found(self) -> None:
        """Test is_available returns False when kind is not found."""
        with patch("shutil.which", return_value=None):
            provider = KindProvider(name="test")
            assert provider.is_available() is False

    def test_is_available_with_kind_command_failure(self, mock_subprocess_run: MagicMock) -> None:
        """Test is_available returns False when kind command fails."""
        mock_subprocess_run.side_effect = CalledProcessError(1, "kind")
        provider = KindProvider(name="test")
        assert provider.is_available() is False

    def test_is_available_with_kubectl_not_found(self) -> None:
        """Test is_available returns False when kubectl is not found."""

        def mock_which(cmd: str) -> str | None:
            return {
                "kind": "/usr/local/bin/kind",
                "kubectl": None,
                "helm": "/usr/local/bin/helm",
            }.get(cmd)

        with (
            patch("shutil.which", side_effect=mock_which),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.stdout = "kind v0.20.0"
            provider = KindProvider(name="test")
            assert provider.is_available() is False

    def test_is_available_with_helm_not_found(self) -> None:
        """Test is_available returns False when helm is not found."""

        def mock_which(cmd: str) -> str | None:
            return {
                "kind": "/usr/local/bin/kind",
                "kubectl": "/usr/local/bin/kubectl",
                "helm": None,
            }.get(cmd)

        with (
            patch("shutil.which", side_effect=mock_which),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.stdout = "kind v0.20.0"
            provider = KindProvider(name="test")
            assert provider.is_available() is False


class TestKindProviderCreateCluster:
    """Test KindProvider cluster creation."""

    def test_create_cluster_success(self, mock_subprocess_run: MagicMock) -> None:
        """Test successful cluster creation."""
        provider = KindProvider(name="demo")

        with (
            patch.object(provider, "_wait_for_cluster_ready"),
            patch.object(provider, "_install_nginx_ingress"),
            patch.object(provider, "_install_argocd"),
        ):
            result = provider.create_cluster()

            assert result is True

            # Verify the cluster creation commands
            actual_calls = mock_subprocess_run.call_args_list
            assert len(actual_calls) == 2  # noqa: PLR2004 # is_available + create cluster

            # The second call should be the cluster creation
            create_call = actual_calls[1]
            assert_command_contains(create_call, ["kind", "create", "cluster", "--name", "demo", "--config"])

    def test_create_cluster_not_available_raises_error(self) -> None:
        """Test create_cluster raises ProviderNotAvailableError when dependencies not available."""
        with patch("shutil.which", return_value=None):
            provider = KindProvider(name="demo")

            with pytest.raises(ProviderNotAvailableError, match="KinD, kubectl, and helm are required"):
                provider.create_cluster()

    def test_create_cluster_command_failure_raises_error(self) -> None:
        """Test create_cluster raises ClusterCreationError when command fails."""
        provider = KindProvider(name="demo")

        with (
            patch.object(provider, "is_available", return_value=True),
            patch("subprocess.run", side_effect=CalledProcessError(1, "kind")),
            pytest.raises(ClusterCreationError, match="Failed to create KinD cluster"),
        ):
            provider.create_cluster()


class TestKindProviderDeleteCluster:
    """Test KindProvider cluster deletion."""

    def test_delete_cluster_success(self, mock_subprocess_run: MagicMock) -> None:
        """Test successful cluster deletion."""
        provider = KindProvider(name="demo")

        result = provider.delete_cluster()

        assert result is True
        # Verify the delete command was called correctly
        call_args = mock_subprocess_run.call_args
        assert_command_contains(call_args, ["kind", "delete", "cluster", "--name", "demo"])

    def test_delete_cluster_with_custom_name(self, mock_subprocess_run: MagicMock) -> None:
        """Test cluster deletion with custom cluster name."""
        provider = KindProvider(name="demo")

        result = provider.delete_cluster(name="custom-cluster")

        assert result is True
        call_args = mock_subprocess_run.call_args
        assert_command_contains(call_args, ["kind", "delete", "cluster", "--name", "custom-cluster"])

    def test_delete_cluster_command_failure_raises_error(self, mock_subprocess_run: MagicMock) -> None:
        """Test delete_cluster raises ClusterOperationError when command fails."""
        mock_subprocess_run.side_effect = CalledProcessError(1, "kind")

        provider = KindProvider(name="demo")

        with pytest.raises(ClusterOperationError, match="Failed to delete KinD cluster 'demo'"):
            provider.delete_cluster()

    def test_delete_cluster_invokes_correct_command_explicit_patch(self) -> None:
        """Test delete_cluster invokes correct command using explicit module patching."""
        with patch("localargo.providers.kind.subprocess.run") as mock_run:
            provider = KindProvider("demo")
            provider.delete_cluster()
            call_args = mock_run.call_args
            assert_command_contains(call_args, ["kind", "delete", "cluster", "--name", "demo"])


class TestKindProviderGetClusterStatus:
    """Test KindProvider cluster status retrieval."""

    def test_get_cluster_status_success(self, mock_subprocess_run: MagicMock) -> None:
        """Test successful cluster status retrieval."""
        # Mock kind get clusters command
        mock_run = MagicMock()
        mock_run.returncode = 0
        mock_run.stdout = "demo\nother-cluster\n"

        # Mock kubectl cluster-info command
        mock_run2 = MagicMock()
        mock_run2.returncode = 0

        mock_subprocess_run.side_effect = [mock_run, mock_run2]

        provider = KindProvider(name="demo")

        status = provider.get_cluster_status()

        expected_status = {
            "provider": "kind",
            "name": "demo",
            "exists": True,
            "context": "kind-demo",
            "ready": True,
        }
        assert status == expected_status
        assert mock_subprocess_run.call_count == 2  # noqa: PLR2004

    def test_get_cluster_status_cluster_not_exists(self) -> None:
        """Test cluster status when cluster doesn't exist."""
        provider = KindProvider(name="demo")

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "other-cluster\n"
            mock_run.return_value = mock_result

            status = provider.get_cluster_status()

            expected_status = {
                "provider": "kind",
                "name": "demo",
                "exists": False,
                "context": "kind-demo",
                "ready": False,
            }
            assert status == expected_status

    def test_get_cluster_status_with_custom_name(self) -> None:
        """Test cluster status retrieval with custom cluster name."""
        provider = KindProvider(name="demo")

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "custom-cluster\nother-cluster\n"
            mock_run.return_value = mock_result

            status = provider.get_cluster_status(name="custom-cluster")

            expected_status = {
                "provider": "kind",
                "name": "custom-cluster",
                "exists": True,
                "context": "kind-custom-cluster",
                "ready": True,
            }
            assert status == expected_status

    def test_get_cluster_status_command_failure_raises_error(self) -> None:
        """Test get_cluster_status raises ClusterOperationError when command fails."""
        provider = KindProvider(name="demo")

        with (
            patch("subprocess.run", side_effect=CalledProcessError(1, "kind")),
            pytest.raises(ClusterOperationError, match="Failed to get cluster status"),
        ):
            provider.get_cluster_status()
