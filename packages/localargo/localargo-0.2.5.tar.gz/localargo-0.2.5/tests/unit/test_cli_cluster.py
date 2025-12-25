"""Tests for CLI cluster commands."""

# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
from subprocess import CalledProcessError
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from localargo.cli.commands.cluster import delete, init, password, status


class TestCLIClusterInit:
    """Test suite for cluster init command."""

    def test_init_command_success(self) -> None:
        """Test init command with successful cluster creation."""
        with patch("localargo.core.cluster.cluster_manager.create_cluster", return_value=True) as mock_create:
            runner = CliRunner()
            result = runner.invoke(init, ["--provider", "kind", "--name", "test-cluster"])

            assert result.exit_code == 0
            mock_create.assert_called_once_with("kind", "test-cluster")

    def test_init_command_failure(self) -> None:
        """Test init command with cluster creation failure."""
        with patch("localargo.core.cluster.cluster_manager.create_cluster", return_value=False) as mock_create:
            runner = CliRunner()
            result = runner.invoke(init, ["--provider", "kind", "--name", "test-cluster"])

            assert result.exit_code == 0  # Command succeeds but logs failure
            mock_create.assert_called_once_with("kind", "test-cluster")

    def test_init_command_with_k3s_provider(self) -> None:
        """Test init command with k3s provider."""
        with patch("localargo.core.cluster.cluster_manager.create_cluster", return_value=True) as mock_create:
            runner = CliRunner()
            result = runner.invoke(init, ["--provider", "k3s", "--name", "test-cluster"])

            assert result.exit_code == 0
            mock_create.assert_called_once_with("k3s", "test-cluster")


class TestCLIClusterDelete:
    """Test suite for cluster delete command."""

    def test_delete_command_success(self) -> None:
        """Test delete command with successful cluster deletion."""
        with patch("localargo.core.cluster.cluster_manager.delete_cluster", return_value=True) as mock_delete:
            runner = CliRunner()
            result = runner.invoke(delete, ["test-cluster", "--provider", "kind"])

            assert result.exit_code == 0
            mock_delete.assert_called_once_with("kind", "test-cluster")

    def test_delete_command_failure(self) -> None:
        """Test delete command with cluster deletion failure."""
        with patch("localargo.core.cluster.cluster_manager.delete_cluster", return_value=False) as mock_delete:
            runner = CliRunner()
            result = runner.invoke(delete, ["test-cluster", "--provider", "kind"])

            assert result.exit_code == 1
            mock_delete.assert_called_once_with("kind", "test-cluster")

    def test_delete_command_with_k3s_provider(self) -> None:
        """Test delete command with k3s provider."""
        with patch("localargo.core.cluster.cluster_manager.delete_cluster", return_value=True) as mock_delete:
            runner = CliRunner()
            result = runner.invoke(delete, ["test-cluster", "--provider", "k3s"])

            assert result.exit_code == 0
            mock_delete.assert_called_once_with("k3s", "test-cluster")

    def test_delete_command_exception_handling(self) -> None:
        """Test delete command with exception during deletion."""
        with patch(
            "localargo.core.cluster.cluster_manager.delete_cluster",
            side_effect=Exception("Test error"),
        ) as mock_delete:
            runner = CliRunner()
            result = runner.invoke(delete, ["test-cluster", "--provider", "kind"])

            assert result.exit_code == 1
            mock_delete.assert_called_once_with("kind", "test-cluster")


class TestCLIClusterStatus:
    """Test suite for cluster status command."""

    def test_status_command_with_context(self) -> None:
        """Test status command with specific context."""
        runner = CliRunner()
        result = runner.invoke(status, ["--context", "kind-test"])

        assert result.exit_code == 0
        assert "Cluster Context" in result.output
        assert "kind-test" in result.output

    def test_status_command_without_context(self) -> None:
        """Test status command without specific context."""
        runner = CliRunner()
        result = runner.invoke(status, [])

        assert result.exit_code == 0
        assert "Cluster Context" in result.output

    def test_status_command_with_argocd_installed(self) -> None:
        """Test status command when ArgoCD is installed."""
        runner = CliRunner()
        result = runner.invoke(status, [])

        assert result.exit_code == 0
        assert "ArgoCD Status" in result.output
        assert "Installed" in result.output


class TestCLIClusterPassword:
    """Test suite for cluster password command."""

    def test_password_command_success(self) -> None:
        """Test password command with successful password retrieval."""
        runner = CliRunner()

        # Mock the subprocess calls for switch_context and get secret
        with patch("localargo.cli.commands.cluster.cluster_manager.switch_context", return_value=True):
            result = runner.invoke(password, ["test-cluster"])

            assert result.exit_code == 0
            # The command should succeed without raising exceptions

    def test_password_command_failure(self, mock_subprocess_run: MagicMock) -> None:
        """Test password command when kubectl fails."""
        runner = CliRunner()

        # Mock subprocess.run to simulate a kubectl failure
        mock_subprocess_run.side_effect = CalledProcessError(1, "kubectl", stderr="NotFound")

        result = runner.invoke(password, ["nonexistent-cluster"])

        # The command should exit with an error code
        assert result.exit_code != 0
