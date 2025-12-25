"""SEOKit - Claude Code toolkit for SEO articles."""
import shutil
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

from seokit.config import get_commands_dir, get_seokit_data_dir

__version__ = version("seokit")

# SEOKit command prefixes for cleanup detection
SEOKIT_COMMAND_PREFIXES = (
    'search-intent', 'top-article', 'create-outline',
    'optimize-outline', 'write-seo', 'seokit-init', 'internal-link'
)


class SEOKitSetupError(Exception):
    """Base exception for SEOKit setup errors."""
    def __init__(self, message: str, error_code: str, context: dict = None):
        self.error_code = error_code
        self.context = context or {}
        super().__init__(message)

    def __str__(self):
        base = f"[{self.error_code}] {super().__str__()}"
        if self.context:
            details = ", ".join(f"{k}={v}" for k, v in self.context.items() if v)
            if details:
                base += f" ({details})"
        return base


def _print_update_banner():
    """Print update banner."""
    import click
    click.echo()
    click.echo("  ╭───────────────────────────────╮")
    click.echo("  │      SEOKit Updating...       │")
    click.echo("  ╰───────────────────────────────╯")
    click.echo()


def _install_commands():
    """
    Copy slash commands to ~/.claude/commands/ on package load.

    Raises:
        PermissionError: When destination directory is not writable
        OSError: When file copy fails
    """
    commands_src = Path(__file__).parent / 'commands'
    commands_dest = get_commands_dir()

    if not commands_src.exists():
        return

    try:
        commands_dest.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(
            f"[INIT_COMMANDS_MKDIR_PERMISSION] Cannot create commands directory '{commands_dest}': {e}"
        ) from e
    except OSError as e:
        raise OSError(
            f"[INIT_COMMANDS_MKDIR_ERROR] Failed to create commands directory '{commands_dest}': "
            f"{type(e).__name__}: {e}"
        ) from e

    for cmd_file in commands_src.glob('*.md'):
        try:
            shutil.copy2(cmd_file, commands_dest / cmd_file.name)
        except PermissionError as e:
            raise PermissionError(
                f"[INIT_COMMANDS_COPY_PERMISSION] Cannot copy command file '{cmd_file.name}' "
                f"to '{commands_dest}': {e}"
            ) from e
        except OSError as e:
            raise OSError(
                f"[INIT_COMMANDS_COPY_ERROR] Failed to copy command file '{cmd_file.name}': "
                f"{type(e).__name__}: {e}"
            ) from e


def _install_scripts():
    """
    Copy scripts to ~/.claude/seokit/scripts/.

    Raises:
        PermissionError: When destination directory is not writable
        OSError: When file copy fails
    """
    scripts_src = Path(__file__).parent / 'scripts'
    scripts_dest = get_seokit_data_dir() / 'scripts'

    if not scripts_src.exists():
        return False

    try:
        scripts_dest.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(
            f"[INIT_SCRIPTS_MKDIR_PERMISSION] Cannot create scripts directory '{scripts_dest}': {e}"
        ) from e
    except OSError as e:
        raise OSError(
            f"[INIT_SCRIPTS_MKDIR_ERROR] Failed to create scripts directory '{scripts_dest}': "
            f"{type(e).__name__}: {e}"
        ) from e

    for script in scripts_src.glob('*.py'):
        try:
            shutil.copy2(script, scripts_dest / script.name)
        except PermissionError as e:
            raise PermissionError(
                f"[INIT_SCRIPTS_COPY_PERMISSION] Cannot copy script '{script.name}' "
                f"to '{scripts_dest}': {e}"
            ) from e
        except OSError as e:
            raise OSError(
                f"[INIT_SCRIPTS_COPY_ERROR] Failed to copy script '{script.name}': "
                f"{type(e).__name__}: {e}"
            ) from e

    return True


def _create_venv():
    """
    Create isolated venv and install dependencies.

    Raises:
        subprocess.CalledProcessError: When venv creation or pip install fails
        PermissionError: When venv directory is not writable
        FileNotFoundError: When Python executable not found
        OSError: When other OS-level errors occur
    """
    venv_path = get_seokit_data_dir() / 'venv'

    if venv_path.exists():
        return True  # Already exists

    # Create venv
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'venv', str(venv_path)],
            check=True,
            capture_output=True,
            timeout=120
        )
    except subprocess.CalledProcessError as e:
        stderr_text = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        raise subprocess.CalledProcessError(
            e.returncode,
            e.cmd,
            output=e.output,
            stderr=f"[INIT_VENV_CREATE_FAILED] Failed to create virtual environment at '{venv_path}'. "
                   f"Exit code: {e.returncode}. Error: {stderr_text[:300]}".encode()
        ) from e
    except subprocess.TimeoutExpired as e:
        raise subprocess.TimeoutExpired(
            e.cmd,
            e.timeout,
            output=e.output,
            stderr=f"[INIT_VENV_TIMEOUT] Creating venv timed out after {e.timeout} seconds".encode()
        ) from e
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"[INIT_VENV_PYTHON_NOT_FOUND] Python executable not found: {sys.executable}. "
            f"Ensure Python is installed and in PATH. Original error: {e}"
        ) from e
    except PermissionError as e:
        raise PermissionError(
            f"[INIT_VENV_PERMISSION] Cannot create venv directory '{venv_path}': {e}"
        ) from e

    # Get pip path (cross-platform)
    if sys.platform == 'win32':
        pip = venv_path / 'Scripts' / 'pip.exe'
    else:
        pip = venv_path / 'bin' / 'pip'

    if not pip.exists():
        raise FileNotFoundError(
            f"[INIT_VENV_PIP_NOT_FOUND] pip executable not found at expected path '{pip}'. "
            f"Venv creation may have failed silently."
        )

    # Install dependencies (suppress output)
    try:
        subprocess.run(
            [str(pip), 'install', '-q', 'requests', 'python-dotenv'],
            check=True,
            capture_output=True,
            timeout=300
        )
    except subprocess.CalledProcessError as e:
        stderr_text = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        raise subprocess.CalledProcessError(
            e.returncode,
            e.cmd,
            output=e.output,
            stderr=f"[INIT_VENV_PIP_INSTALL_FAILED] Failed to install dependencies. "
                   f"Exit code: {e.returncode}. Error: {stderr_text[:300]}".encode()
        ) from e
    except subprocess.TimeoutExpired as e:
        raise subprocess.TimeoutExpired(
            e.cmd,
            e.timeout,
            output=e.output,
            stderr=f"[INIT_VENV_PIP_TIMEOUT] pip install timed out after {e.timeout} seconds".encode()
        ) from e

    return True


def _is_setup_complete() -> bool:
    """Check if seokit setup has been run."""
    seokit_dir = get_seokit_data_dir()
    return (
        (seokit_dir / 'scripts').exists() and
        (seokit_dir / 'venv').exists()
    )


def _update_checklists(overwrite=False):
    """
    Copy checklists. Skip existing unless overwrite=True.

    Raises:
        PermissionError: When destination directory is not writable
        OSError: When file copy fails
    """
    src = Path(__file__).parent / 'checklists'
    dest = get_seokit_data_dir() / 'checklists'

    if not src.exists():
        return

    try:
        dest.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(
            f"[INIT_CHECKLISTS_MKDIR_PERMISSION] Cannot create checklists directory '{dest}': {e}"
        ) from e
    except OSError as e:
        raise OSError(
            f"[INIT_CHECKLISTS_MKDIR_ERROR] Failed to create checklists directory '{dest}': "
            f"{type(e).__name__}: {e}"
        ) from e

    for file in src.glob('*.md'):
        dest_file = dest / file.name
        if not overwrite and dest_file.exists():
            continue
        try:
            shutil.copy2(file, dest_file)
        except PermissionError as e:
            raise PermissionError(
                f"[INIT_CHECKLISTS_COPY_PERMISSION] Cannot copy checklist '{file.name}' "
                f"to '{dest}': {e}"
            ) from e
        except OSError as e:
            raise OSError(
                f"[INIT_CHECKLISTS_COPY_ERROR] Failed to copy checklist '{file.name}': "
                f"{type(e).__name__}: {e}"
            ) from e


def _cleanup_obsolete_commands():
    """
    Remove SEOKit slash commands no longer in package.

    Raises:
        PermissionError: When file cannot be deleted
        OSError: When file deletion fails
    """
    src = Path(__file__).parent / 'commands'
    dest = get_commands_dir()

    if not src.exists() or not dest.exists():
        return

    package_commands = {f.name for f in src.glob('*.md')}

    for installed in dest.glob('*.md'):
        if installed.name.startswith(SEOKIT_COMMAND_PREFIXES):
            if installed.name not in package_commands:
                try:
                    installed.unlink()
                except PermissionError as e:
                    raise PermissionError(
                        f"[INIT_CLEANUP_CMD_PERMISSION] Cannot delete obsolete command '{installed}': {e}"
                    ) from e
                except OSError as e:
                    raise OSError(
                        f"[INIT_CLEANUP_CMD_ERROR] Failed to delete obsolete command '{installed}': "
                        f"{type(e).__name__}: {e}"
                    ) from e


def _cleanup_obsolete_scripts():
    """
    Remove SEOKit scripts no longer in package.

    Raises:
        PermissionError: When file cannot be deleted
        OSError: When file deletion fails
    """
    src = Path(__file__).parent / 'scripts'
    dest = get_seokit_data_dir() / 'scripts'

    if not src.exists() or not dest.exists():
        return

    package_scripts = {f.name for f in src.glob('*.py')}

    for installed in dest.glob('*.py'):
        if installed.name not in package_scripts:
            try:
                installed.unlink()
            except PermissionError as e:
                raise PermissionError(
                    f"[INIT_CLEANUP_SCRIPT_PERMISSION] Cannot delete obsolete script '{installed}': {e}"
                ) from e
            except OSError as e:
                raise OSError(
                    f"[INIT_CLEANUP_SCRIPT_ERROR] Failed to delete obsolete script '{installed}': "
                    f"{type(e).__name__}: {e}"
                ) from e


def _install_docs():
    """
    Copy docs to ~/.claude/seokit/docs/.

    Raises:
        PermissionError: When destination directory is not writable
        OSError: When file copy fails
    """
    docs_src = Path(__file__).parent / 'docs'
    docs_dest = get_seokit_data_dir() / 'docs'

    if not docs_src.exists():
        return

    try:
        docs_dest.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(
            f"[INIT_DOCS_MKDIR_PERMISSION] Cannot create docs directory '{docs_dest}': {e}"
        ) from e
    except OSError as e:
        raise OSError(
            f"[INIT_DOCS_MKDIR_ERROR] Failed to create docs directory '{docs_dest}': "
            f"{type(e).__name__}: {e}"
        ) from e

    for doc_file in docs_src.glob('*.md'):
        try:
            shutil.copy2(doc_file, docs_dest / doc_file.name)
        except PermissionError as e:
            raise PermissionError(
                f"[INIT_DOCS_COPY_PERMISSION] Cannot copy doc '{doc_file.name}' "
                f"to '{docs_dest}': {e}"
            ) from e
        except OSError as e:
            raise OSError(
                f"[INIT_DOCS_COPY_ERROR] Failed to copy doc '{doc_file.name}': "
                f"{type(e).__name__}: {e}"
            ) from e
