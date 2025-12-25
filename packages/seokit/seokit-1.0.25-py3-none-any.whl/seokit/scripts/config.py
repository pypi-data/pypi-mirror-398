"""
SEOKit Configuration Module
Supports global installation with environment variables.

Error Codes:
    CONFIG_HOME_NOT_FOUND: SEOKIT_HOME directory doesn't exist
    CONFIG_ENV_NOT_FOUND: .env file not found (warning, uses fallback)
    CONFIG_ENV_PARSE_ERROR: .env file exists but couldn't be parsed
    CONFIG_API_KEY_MISSING: PERPLEXITY_API_KEY not set
    CONFIG_API_KEY_PLACEHOLDER: API key is still placeholder value
    CONFIG_OUTPUT_DIR_ERROR: Cannot create output directory
"""
import os
from pathlib import Path


class ConfigError(Exception):
    """Base exception for configuration errors."""
    def __init__(self, message: str, error_code: str, context: dict = None):
        self.error_code = error_code
        self.context = context or {}
        super().__init__(message)

    def __str__(self):
        base = f"[{self.error_code}] {super().__str__()}"
        if self.context:
            details = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base += f" ({details})"
        return base


class EnvLoadError(ConfigError):
    """Raised when .env file cannot be loaded."""
    pass


class OutputDirError(ConfigError):
    """Raised when output directory cannot be created."""
    pass


# Global installation path (default: ~/.claude/seokit)
SEOKIT_HOME = Path(os.getenv("SEOKIT_HOME", Path.home() / ".claude" / "seokit"))

# Load .env with detailed error tracking
env_path = SEOKIT_HOME / ".env"
_env_load_status = {"loaded": False, "path": None, "fallback": False, "error": None}

try:
    from dotenv import load_dotenv

    if env_path.exists():
        try:
            load_dotenv(env_path)
            _env_load_status = {"loaded": True, "path": str(env_path), "fallback": False, "error": None}
        except Exception as e:
            _env_load_status = {
                "loaded": False,
                "path": str(env_path),
                "fallback": False,
                "error": f"Failed to parse .env: {type(e).__name__}: {e}"
            }
            # Still try local fallback
            load_dotenv()
            _env_load_status["fallback"] = True
    else:
        # Fallback to local .env for development
        load_dotenv()
        _env_load_status = {"loaded": True, "path": "local", "fallback": True, "error": None}
except ImportError as e:
    _env_load_status = {
        "loaded": False,
        "path": None,
        "fallback": False,
        "error": f"python-dotenv not installed: {e}"
    }

# Output directory - keyword folder in current working directory
KEYWORD_SLUG = os.getenv("SEOKIT_KEYWORD", "")
if KEYWORD_SLUG:
    OUTPUTS_DIR = Path.cwd() / KEYWORD_SLUG
else:
    # Fallback to local outputs for development
    OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"

# Checklists from global location
CHECKLISTS_DIR = SEOKIT_HOME / "checklists"
if not CHECKLISTS_DIR.exists():
    # Fallback for development
    CHECKLISTS_DIR = Path(__file__).parent.parent / "checklists"

# Ensure output directory exists with error tracking
_output_dir_status = {"created": False, "path": None, "error": None}
try:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    _output_dir_status = {"created": True, "path": str(OUTPUTS_DIR), "error": None}
except PermissionError as e:
    _output_dir_status = {
        "created": False,
        "path": str(OUTPUTS_DIR),
        "error": f"Permission denied creating output directory: {e}"
    }
except OSError as e:
    _output_dir_status = {
        "created": False,
        "path": str(OUTPUTS_DIR),
        "error": f"OS error creating output directory: {type(e).__name__}: {e}"
    }

# API Configuration
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "sonar-pro"


def get_env_status() -> dict:
    """Return the status of .env loading for debugging."""
    return _env_load_status.copy()


def get_output_dir_status() -> dict:
    """Return the status of output directory creation for debugging."""
    return _output_dir_status.copy()


def validate_config() -> dict:
    """
    Comprehensive configuration validation with detailed error info.

    Returns:
        dict with structure:
            - valid (bool): Whether config is valid
            - error_code (str): Machine-readable error code
            - error_message (str): Human-readable error message
            - env_path (str): Path to .env file
            - suggestion (str): How to fix the issue
            - diagnostics (dict): Additional debug info
    """
    diagnostics = {
        "seokit_home": str(SEOKIT_HOME),
        "seokit_home_exists": SEOKIT_HOME.exists(),
        "env_status": _env_load_status,
        "output_dir_status": _output_dir_status,
        "api_key_set": bool(PERPLEXITY_API_KEY),
        "api_key_length": len(PERPLEXITY_API_KEY) if PERPLEXITY_API_KEY else 0,
    }

    # Check if python-dotenv failed to load
    if _env_load_status.get("error") and "not installed" in _env_load_status["error"]:
        return {
            "valid": False,
            "error_code": "CONFIG_DOTENV_MISSING",
            "error_message": "python-dotenv package not installed",
            "env_path": str(SEOKIT_HOME / ".env"),
            "suggestion": "Run: pip install python-dotenv",
            "diagnostics": diagnostics
        }

    # Check if .env file had parse errors
    if _env_load_status.get("error") and "Failed to parse" in _env_load_status["error"]:
        return {
            "valid": False,
            "error_code": "CONFIG_ENV_PARSE_ERROR",
            "error_message": f".env file exists but couldn't be parsed: {_env_load_status['error']}",
            "env_path": str(env_path),
            "suggestion": "Check .env file syntax (should be KEY=value format, no quotes needed)",
            "diagnostics": diagnostics
        }

    # Check if output directory couldn't be created
    if _output_dir_status.get("error"):
        return {
            "valid": False,
            "error_code": "CONFIG_OUTPUT_DIR_ERROR",
            "error_message": _output_dir_status["error"],
            "env_path": str(SEOKIT_HOME / ".env"),
            "suggestion": f"Check write permissions for: {OUTPUTS_DIR.parent}",
            "diagnostics": diagnostics
        }

    # Check if API key is missing
    if not PERPLEXITY_API_KEY:
        return {
            "valid": False,
            "error_code": "CONFIG_API_KEY_MISSING",
            "error_message": "PERPLEXITY_API_KEY environment variable not set",
            "env_path": str(SEOKIT_HOME / ".env"),
            "suggestion": f"Add PERPLEXITY_API_KEY=pplx-xxxx to {SEOKIT_HOME / '.env'}",
            "diagnostics": diagnostics
        }

    # Check if API key is still placeholder
    if PERPLEXITY_API_KEY.startswith("pplx-xxx"):
        return {
            "valid": False,
            "error_code": "CONFIG_API_KEY_PLACEHOLDER",
            "error_message": "PERPLEXITY_API_KEY is still set to placeholder value",
            "env_path": str(SEOKIT_HOME / ".env"),
            "suggestion": "Replace placeholder with your actual API key from https://perplexity.ai/settings/api",
            "diagnostics": diagnostics
        }

    # Check if API key format looks valid (basic sanity check)
    if not PERPLEXITY_API_KEY.startswith("pplx-"):
        return {
            "valid": False,
            "error_code": "CONFIG_API_KEY_INVALID_FORMAT",
            "error_message": f"PERPLEXITY_API_KEY doesn't start with 'pplx-' (got: {PERPLEXITY_API_KEY[:10]}...)",
            "env_path": str(SEOKIT_HOME / ".env"),
            "suggestion": "Perplexity API keys should start with 'pplx-'. Get your key from https://perplexity.ai/settings/api",
            "diagnostics": diagnostics
        }

    return {"valid": True, "diagnostics": diagnostics}
