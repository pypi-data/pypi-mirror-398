"""Tests for seokit/__init__.py helper functions."""

# Assume PYTHONPATH=src is set for these imports to work
from seokit import (
    SEOKIT_COMMAND_PREFIXES,
    __version__,
    _cleanup_obsolete_commands,
    _install_commands,
    _print_update_banner,
    _update_checklists,
)


# 1. Module imports correctly
def test_module_imports():
    """Verify all helper functions are importable."""
    assert _print_update_banner is not None
    assert _update_checklists is not None
    assert _cleanup_obsolete_commands is not None
    assert _install_commands is not None
    assert SEOKIT_COMMAND_PREFIXES is not None
    assert __version__ is not None


def test_seokit_command_prefixes():
    """Verify SEOKIT_COMMAND_PREFIXES contains expected values."""
    expected = ('search-intent', 'top-article', 'create-outline', 'optimize-outline', 'write-seo', 'seokit-init', 'internal-link')
    assert expected == SEOKIT_COMMAND_PREFIXES


def test_version_format():
    """Verify version string is valid semver format."""
    parts = __version__.split('.')
    assert len(parts) == 3
    for part in parts:
        assert part.isdigit()


# 2. _print_update_banner() displays box banner
def test_print_update_banner(capsys):
    """Verify banner displays correctly."""
    _print_update_banner()
    captured = capsys.readouterr()
    assert "╭───────────────────────────────╮" in captured.out
    assert "│      SEOKit Updating...       │" in captured.out
    assert "╰───────────────────────────────╯" in captured.out


# 3. _update_checklists function signature
def test_update_checklists_accepts_overwrite_param():
    """Verify _update_checklists accepts overwrite parameter."""
    import inspect
    sig = inspect.signature(_update_checklists)
    assert 'overwrite' in sig.parameters
    assert sig.parameters['overwrite'].default is False


# 4. _cleanup_obsolete_commands function exists
def test_cleanup_obsolete_commands_callable():
    """Verify _cleanup_obsolete_commands is callable."""
    assert callable(_cleanup_obsolete_commands)
