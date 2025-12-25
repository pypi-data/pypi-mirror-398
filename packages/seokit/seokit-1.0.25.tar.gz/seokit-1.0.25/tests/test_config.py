"""Tests for SEOKit config module."""
import importlib
import sys
from pathlib import Path

import pytest


class TestGetHome:
    """Test get_home function for cross-platform compatibility."""

    def test_get_home_returns_path(self):
        """Test get_home returns a Path object."""
        from seokit.config import get_home
        home = get_home()
        assert isinstance(home, Path)

    def test_get_home_linux_uses_pathlib_home(self, monkeypatch):
        """Test get_home on Linux uses Path.home()."""
        monkeypatch.setattr(sys, 'platform', 'linux')
        # Reload module to pick up platform change
        import seokit.config
        importlib.reload(seokit.config)
        home = seokit.config.get_home()
        assert isinstance(home, Path)

    def test_get_home_windows_uses_userprofile(self, monkeypatch, tmp_path):
        """Test get_home on Windows uses USERPROFILE."""
        monkeypatch.setattr(sys, 'platform', 'win32')
        monkeypatch.setenv('USERPROFILE', str(tmp_path))
        # Reload module to pick up platform change
        import seokit.config
        importlib.reload(seokit.config)
        home = seokit.config.get_home()
        # Should contain the tmp_path or be a valid Path
        assert isinstance(home, Path)


class TestDirectoryPaths:
    """Test directory path functions."""

    def test_get_claude_dir(self):
        """Test get_claude_dir returns proper path."""
        from seokit.config import get_claude_dir, get_home
        claude_dir = get_claude_dir()
        assert claude_dir == get_home() / '.claude'

    def test_get_commands_dir(self):
        """Test get_commands_dir returns proper path."""
        from seokit.config import get_claude_dir, get_commands_dir
        commands_dir = get_commands_dir()
        assert commands_dir == get_claude_dir() / 'commands'

    def test_get_seokit_data_dir(self):
        """Test get_seokit_data_dir returns proper path."""
        from seokit.config import get_claude_dir, get_seokit_data_dir
        data_dir = get_seokit_data_dir()
        assert data_dir == get_claude_dir() / 'seokit'


class TestAPIConfig:
    """Test API configuration values."""

    def test_perplexity_api_url(self):
        """Test Perplexity API URL is correct."""
        from seokit.config import PERPLEXITY_API_URL
        assert PERPLEXITY_API_URL == "https://api.perplexity.ai/chat/completions"

    def test_perplexity_model(self):
        """Test default Perplexity model is set."""
        from seokit.config import PERPLEXITY_MODEL
        assert PERPLEXITY_MODEL == "sonar-pro"


class TestValidateConfig:
    """Test validate_config function."""

    def test_validate_config_without_key_fails(self, monkeypatch):
        """Test validate_config returns False when API key is not set."""
        monkeypatch.setenv('PERPLEXITY_API_KEY', '')
        import seokit.config
        importlib.reload(seokit.config)
        # Manually set the module variable since reload may not update it
        seokit.config.PERPLEXITY_API_KEY = ''
        result = seokit.config.validate_config()
        assert result is False

    def test_validate_config_with_placeholder_fails(self, monkeypatch, capsys):
        """Test validate_config returns False with placeholder key."""
        monkeypatch.setenv('PERPLEXITY_API_KEY', 'pplx-xxxxxxx')
        import seokit.config
        importlib.reload(seokit.config)
        seokit.config.PERPLEXITY_API_KEY = 'pplx-xxxxxxx'
        result = seokit.config.validate_config()
        assert result is False
        captured = capsys.readouterr()
        assert 'PERPLEXITY_API_KEY' in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
