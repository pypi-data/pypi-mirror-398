# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Tests for CA CLI commands."""

from unittest.mock import MagicMock, Mock

from click.testing import CliRunner

from localargo.cli.commands.ca import ca_status_cmd


class TestCAStatusCommand:
    """Test cases for CA status command."""

    def test_ca_status_command_success(self, mock_subprocess_run: MagicMock) -> None:
        """Test CA status command with all components present."""
        # Mock kubectl calls to succeed
        mock_success = Mock()
        mock_success.returncode = 0
        mock_success.stdout = "True"
        mock_subprocess_run.return_value = mock_success

        runner = CliRunner()
        result = runner.invoke(ca_status_cmd)

        assert result.exit_code == 0
        # Check that the status table is displayed
        assert "Certificate Authority Status" in result.output

    def test_ca_status_command_missing_components(self, mock_subprocess_run: MagicMock) -> None:
        """Test CA status command with missing components."""
        # Mock kubectl calls to fail (components missing)
        mock_missing = Mock()
        mock_missing.returncode = 1
        mock_missing.stdout = ""
        mock_subprocess_run.return_value = mock_missing

        runner = CliRunner()
        result = runner.invoke(ca_status_cmd)

        assert result.exit_code == 0
        # Just check that the command runs and shows the table
        assert "Certificate Authority Status" in result.output
