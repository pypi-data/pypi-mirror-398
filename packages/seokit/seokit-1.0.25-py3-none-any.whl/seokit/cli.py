"""SEOKit CLI - Claude Code toolkit for SEO articles."""
import re
import shutil
import subprocess
import sys

import click

from seokit import (
    __version__,
    _cleanup_obsolete_commands,
    _cleanup_obsolete_scripts,
    _create_venv,
    _install_commands,
    _install_docs,
    _install_scripts,
    _is_setup_complete,
    _print_update_banner,
    _update_checklists,
)
from seokit.config import (
    PERPLEXITY_API_KEY,
    get_claude_dir,
    get_commands_dir,
    get_seokit_data_dir,
)

# Slash command files to remove
SLASH_COMMANDS = [
    'create-outline.md',
    'internal-link.md',
    'internal-link:list.md',
    'internal-link:sync.md',
    'optimize-outline.md',
    'search-intent.md',
    'seokit-init.md',
    'top-article.md',
    'write-seo.md',
]


@click.group(invoke_without_command=True)
@click.version_option(
    version=__version__,
    prog_name="SeoKit",
    message="%(prog)s Version: v%(version)s"
)
@click.pass_context
def main(ctx):
    """SEOKit - Claude Code toolkit for creating high-quality SEO articles."""
    # If no subcommand provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        return

    # Skip validation for setup command
    if ctx.invoked_subcommand == 'setup':
        return

    # Warn if setup not complete
    if not _is_setup_complete():
        click.echo("SEOKit not configured. Run: seokit setup")
        ctx.exit(1)


@main.command()
def config():
    """Configure SEOKit (API keys, settings)."""
    env_file = get_claude_dir() / '.env'

    click.echo("SEOKit Configuration")
    click.echo("-" * 40)

    # Check current API key
    if PERPLEXITY_API_KEY:
        if len(PERPLEXITY_API_KEY) > 12:
            masked = PERPLEXITY_API_KEY[:8] + "..." + PERPLEXITY_API_KEY[-4:]
        else:
            masked = "***"
        click.echo(f"Current Perplexity API Key: {masked}")
    else:
        click.echo("Perplexity API Key: Not set")

    # Prompt for new key
    new_key = click.prompt(
        "Enter new Perplexity API Key (or press Enter to skip)",
        default="",
        show_default=False
    )

    if new_key:
        env_file.parent.mkdir(parents=True, exist_ok=True)

        if env_file.exists():
            content = env_file.read_text()
            if 'PERPLEXITY_API_KEY' in content:
                content = re.sub(
                    r'PERPLEXITY_API_KEY=.*',
                    f'PERPLEXITY_API_KEY={new_key}',
                    content
                )
            else:
                content = content.rstrip() + f'\nPERPLEXITY_API_KEY={new_key}\n'
        else:
            content = f'PERPLEXITY_API_KEY={new_key}\n'

        env_file.write_text(content)
        click.echo("API Key updated!")
    else:
        click.echo("Skipped - no changes made")


@main.command()
def setup():
    """Install SEOKit runtime files (commands, scripts, venv)."""
    click.echo("Setting up SEOKit...")

    # Install slash commands
    try:
        _install_commands()
    except PermissionError as e:
        click.echo(f"[SETUP_COMMANDS_PERMISSION] Cannot write slash commands: {e}")
        click.echo(f"  Check write permissions for: {get_commands_dir()}")
        return
    except OSError as e:
        click.echo(f"[SETUP_COMMANDS_ERROR] Failed to install slash commands: {type(e).__name__}: {e}")
        return

    # Install scripts
    try:
        _install_scripts()
    except PermissionError as e:
        click.echo(f"[SETUP_SCRIPTS_PERMISSION] Cannot write scripts: {e}")
        click.echo(f"  Check write permissions for: {get_seokit_data_dir() / 'scripts'}")
        return
    except OSError as e:
        click.echo(f"[SETUP_SCRIPTS_ERROR] Failed to install scripts: {type(e).__name__}: {e}")
        return

    # Create venv
    try:
        _create_venv()
    except subprocess.CalledProcessError as e:
        click.echo(f"[SETUP_VENV_SUBPROCESS] Failed to create virtual environment")
        click.echo(f"  Command: {' '.join(e.cmd) if isinstance(e.cmd, list) else e.cmd}")
        click.echo(f"  Exit code: {e.returncode}")
        if e.stderr:
            stderr_text = e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr
            click.echo(f"  Error output: {stderr_text[:300]}")
        return
    except PermissionError as e:
        click.echo(f"[SETUP_VENV_PERMISSION] Cannot create venv directory: {e}")
        click.echo(f"  Check write permissions for: {get_seokit_data_dir()}")
        return
    except FileNotFoundError as e:
        click.echo(f"[SETUP_VENV_PYTHON_NOT_FOUND] Python executable not found: {e}")
        click.echo(f"  Ensure Python is installed and in your PATH")
        return
    except OSError as e:
        click.echo(f"[SETUP_VENV_ERROR] Failed to create venv: {type(e).__name__}: {e}")
        return

    # Install checklists
    try:
        _update_checklists()
    except PermissionError as e:
        click.echo(f"[SETUP_CHECKLISTS_PERMISSION] Cannot write checklists: {e}")
        click.echo(f"  Check write permissions for: {get_seokit_data_dir() / 'checklists'}")
        return
    except OSError as e:
        click.echo(f"[SETUP_CHECKLISTS_ERROR] Failed to install checklists: {type(e).__name__}: {e}")
        return

    # Install docs (seo-guidelines)
    try:
        _install_docs()
    except PermissionError as e:
        click.echo(f"[SETUP_DOCS_PERMISSION] Cannot write docs: {e}")
        click.echo(f"  Check write permissions for: {get_seokit_data_dir() / 'docs'}")
        return
    except OSError as e:
        click.echo(f"[SETUP_DOCS_ERROR] Failed to install docs: {type(e).__name__}: {e}")
        return

    click.echo("SEOKit setup complete!")
    click.echo("")
    click.echo("Run 'seokit config' to set your Perplexity API key.")


@main.command()
@click.option('--force', '-f', is_flag=True, help='Overwrite all files including user customizations')
def update(force: bool):
    """Update SEOKit files (preserves user customizations)."""
    _print_update_banner()

    # Self-update from PyPI using pipx or pip
    click.echo("Checking for updates...")
    upgrade_success = False
    try:
        result = subprocess.run(
            ['pipx', 'upgrade', 'seokit'],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            upgrade_success = True
        else:
            # pipx upgrade failed - try pipx install (for pip-installed packages)
            result = subprocess.run(
                ['pipx', 'install', 'seokit', '--force'],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                upgrade_success = True
            else:
                # Fallback to pip with --break-system-packages (PEP 668)
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '--upgrade',
                     '--break-system-packages', 'seokit'],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    upgrade_success = True
                else:
                    click.echo(f"[UPDATE_PIP_FAILED] pip upgrade failed (exit {result.returncode})")
                    if result.stderr:
                        click.echo(f"  Error: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        click.echo("[UPDATE_TIMEOUT] Package upgrade timed out after 120 seconds")
        click.echo("  Check your network connection and try again")
    except FileNotFoundError:
        click.echo("[UPDATE_PIPX_NOT_FOUND] pipx not found, trying pip...")
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade',
                 '--break-system-packages', 'seokit'],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                upgrade_success = True
        except subprocess.TimeoutExpired:
            click.echo("[UPDATE_PIP_TIMEOUT] pip upgrade timed out after 120 seconds")

    # Get version from fresh Python process (avoids metadata cache)
    try:
        result = subprocess.run(
            [sys.executable, '-c', 'from importlib.metadata import version; print(version("seokit"))'],
            capture_output=True,
            text=True,
            timeout=10
        )
        new_version = result.stdout.strip() if result.returncode == 0 else __version__
    except (subprocess.TimeoutExpired, OSError):
        new_version = __version__

    # Slash commands: overwrite + cleanup obsolete
    try:
        _install_commands()
        _cleanup_obsolete_commands()
    except PermissionError as e:
        click.echo(f"[UPDATE_COMMANDS_PERMISSION] Cannot update slash commands: {e}")
        click.echo(f"  Check write permissions for: {get_commands_dir()}")
    except OSError as e:
        click.echo(f"[UPDATE_COMMANDS_ERROR] Failed to update commands: {type(e).__name__}: {e}")

    # Update scripts + cleanup obsolete
    try:
        _install_scripts()
        _cleanup_obsolete_scripts()
        click.echo("  + Scripts updated")
    except PermissionError as e:
        click.echo(f"[UPDATE_SCRIPTS_PERMISSION] Cannot update scripts: {e}")
        click.echo(f"  Check write permissions for: {get_seokit_data_dir() / 'scripts'}")
    except OSError as e:
        click.echo(f"[UPDATE_SCRIPTS_ERROR] Failed to update scripts: {type(e).__name__}: {e}")

    # Checklists: merge or force overwrite
    try:
        _update_checklists(overwrite=force)
    except PermissionError as e:
        click.echo(f"[UPDATE_CHECKLISTS_PERMISSION] Cannot update checklists: {e}")
    except OSError as e:
        click.echo(f"[UPDATE_CHECKLISTS_ERROR] Failed to update checklists: {type(e).__name__}: {e}")

    # Update docs (seo-guidelines)
    try:
        _install_docs()
    except PermissionError as e:
        click.echo(f"[UPDATE_DOCS_PERMISSION] Cannot update docs: {e}")
    except OSError as e:
        click.echo(f"[UPDATE_DOCS_ERROR] Failed to update docs: {type(e).__name__}: {e}")

    # Output success message
    if force:
        click.echo(f"SEOKit v{new_version} - Reset to defaults!")
    else:
        click.echo(f"SEOKit v{new_version} - Updated successfully!")


@main.command()
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
def uninstall(yes: bool):
    """Completely remove SEOKit from the system."""
    seokit_dir = get_seokit_data_dir()
    commands_dir = get_commands_dir()

    click.echo("SEOKit Uninstaller")
    click.echo("=" * 40)
    click.echo("")
    click.echo("This will remove:")
    click.echo(f"  - {seokit_dir}/ (scripts, venv, config)")

    # Check which commands exist
    existing_commands = []
    for cmd in SLASH_COMMANDS:
        cmd_path = commands_dir / cmd
        if cmd_path.exists():
            existing_commands.append(cmd)

    if existing_commands:
        click.echo(f"  - Slash commands from {commands_dir}/:")
        for cmd in existing_commands:
            click.echo(f"      {cmd}")

    click.echo("")

    if not yes:
        if not click.confirm("Continue?", default=False):
            click.echo("Cancelled.")
            return

    click.echo("")

    # Remove seokit data directory
    if seokit_dir.exists():
        try:
            shutil.rmtree(seokit_dir)
            click.echo(f"Removed: {seokit_dir}/")
        except PermissionError as e:
            click.echo(f"[UNINSTALL_DIR_PERMISSION] Cannot remove {seokit_dir}/: {e}")
            click.echo(f"  Try: sudo rm -rf {seokit_dir}")
        except OSError as e:
            click.echo(f"[UNINSTALL_DIR_ERROR] Failed to remove {seokit_dir}/: {type(e).__name__}: {e}")

    # Remove slash commands
    for cmd in SLASH_COMMANDS:
        cmd_path = commands_dir / cmd
        if cmd_path.exists():
            try:
                cmd_path.unlink()
                click.echo(f"Removed: {cmd_path}")
            except PermissionError as e:
                click.echo(f"[UNINSTALL_CMD_PERMISSION] Cannot remove {cmd_path}: {e}")
            except OSError as e:
                click.echo(f"[UNINSTALL_CMD_ERROR] Failed to remove {cmd_path}: {type(e).__name__}: {e}")

    click.echo("")
    click.echo("=" * 40)
    click.echo("SEOKit uninstalled successfully!")

    # Uninstall package (try pipx first, fallback to pip)
    click.echo("")
    click.echo("Uninstalling package...")

    # Try pipx first
    try:
        result = subprocess.run(
            ['pipx', 'uninstall', 'seokit'],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            click.echo("Removed: seokit (pipx)")
        else:
            # Fallback to pip
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'uninstall', '-y', 'seokit'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                click.echo("Removed: seokit (pip)")
            elif "not installed" in result.stderr.lower():
                click.echo("Note: package already removed")
            else:
                click.echo("")
                click.echo(f"[UNINSTALL_PKG_FAILED] Could not auto-remove package (exit {result.returncode})")
                if result.stderr:
                    click.echo(f"  Error: {result.stderr[:200]}")
                click.echo("Please run manually:")
                click.echo("  pipx uninstall seokit")
                click.echo("  # or")
                click.echo(f"  {sys.executable} -m pip uninstall seokit")
    except subprocess.TimeoutExpired:
        click.echo("[UNINSTALL_PKG_TIMEOUT] Package uninstall timed out after 60 seconds")
        click.echo("Please run manually:")
        click.echo("  pipx uninstall seokit")
    except FileNotFoundError:
        # pipx not found, try pip directly
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'uninstall', '-y', 'seokit'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                click.echo("Removed: seokit (pip)")
            else:
                click.echo(f"[UNINSTALL_PIP_FAILED] pip uninstall failed (exit {result.returncode})")
                if result.stderr:
                    click.echo(f"  Error: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            click.echo("[UNINSTALL_PIP_TIMEOUT] pip uninstall timed out")
        except OSError as e:
            click.echo(f"[UNINSTALL_PIP_ERROR] Failed to run pip: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
