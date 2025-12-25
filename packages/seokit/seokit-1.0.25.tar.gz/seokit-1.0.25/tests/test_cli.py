"""Tests for SEOKit CLI."""
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from seokit.cli import main


@pytest.fixture
def runner():
    """Create Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_setup_complete():
    """Mock _is_setup_complete to return True."""
    with patch("seokit.cli._is_setup_complete", return_value=True):
        yield


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_help_shows_all_commands(self, runner):
        """Test --help shows all expected commands."""
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        # Only config and uninstall remain after simplification
        assert 'config' in result.output
        assert 'uninstall' in result.output

    def test_version_flag(self, runner):
        """Test --version shows version info in correct format."""
        result = runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert "SeoKit Version: v" in result.output


class TestConfigCommand:
    """Test config command."""

    def test_config_help(self, runner):
        """Test config --help works."""
        result = runner.invoke(main, ['config', '--help'])
        assert result.exit_code == 0

    def test_config_shows_current_state(self, runner, tmp_path, monkeypatch, mock_setup_complete):
        """Test config command shows current configuration."""
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('USERPROFILE', str(tmp_path))
        # Skip the prompt by sending empty input
        result = runner.invoke(main, ['config'], input='\n')
        assert result.exit_code == 0
        assert 'Configuration' in result.output


class TestUninstallCommand:
    """Test uninstall command."""

    def test_uninstall_help(self, runner):
        """Test uninstall --help works."""
        result = runner.invoke(main, ['uninstall', '--help'])
        assert result.exit_code == 0
        assert '--yes' in result.output or '-y' in result.output

    def test_uninstall_cancelled(self, runner, tmp_path, monkeypatch, mock_setup_complete):
        """Test uninstall command can be cancelled."""
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('USERPROFILE', str(tmp_path))

        # Answer 'n' to confirmation
        result = runner.invoke(main, ['uninstall'], input='n\n')
        assert result.exit_code == 0
        assert 'Cancelled' in result.output

    def test_uninstall_with_yes_flag(self, runner, tmp_path, monkeypatch, mock_setup_complete):
        """Test uninstall with -y flag skips confirmation."""
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('USERPROFILE', str(tmp_path))

        result = runner.invoke(main, ['uninstall', '-y'])
        assert result.exit_code == 0
        assert 'uninstalled successfully' in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
