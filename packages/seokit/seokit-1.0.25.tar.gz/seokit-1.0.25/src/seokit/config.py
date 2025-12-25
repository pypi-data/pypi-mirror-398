"""
SEOKit Configuration Module - Platform-aware paths for cross-platform support.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def get_home() -> Path:
    """Get user home directory (cross-platform)."""
    if sys.platform == 'win32':
        return Path(os.environ.get('USERPROFILE', Path.home()))
    return Path.home()


def get_claude_dir() -> Path:
    """Get Claude config directory."""
    return get_home() / '.claude'


def get_commands_dir() -> Path:
    """Get Claude commands directory."""
    return get_claude_dir() / 'commands'


def get_seokit_data_dir() -> Path:
    """Get SEOKit data directory for outputs."""
    return get_claude_dir() / 'seokit'


# Global installation path (default: ~/.claude/seokit)
SEOKIT_HOME = Path(os.getenv("SEOKIT_HOME", get_seokit_data_dir()))

# Load .env from Claude directory first, then seokit, then local
env_path = get_claude_dir() / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    env_path = SEOKIT_HOME / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

# Output directory - keyword folder in current working directory
KEYWORD_SLUG = os.getenv("SEOKIT_KEYWORD", "")
if KEYWORD_SLUG:
    OUTPUTS_DIR = Path.cwd() / KEYWORD_SLUG
else:
    OUTPUTS_DIR = Path.cwd() / "outputs"

# Checklists from global location
CHECKLISTS_DIR = SEOKIT_HOME / "checklists"
if not CHECKLISTS_DIR.exists():
    CHECKLISTS_DIR = Path(__file__).parent.parent.parent.parent / "checklists"

# Ensure output directory exists
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# API Configuration
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "sonar-pro"


def validate_config() -> bool:
    """Check if required configuration is present."""
    if not PERPLEXITY_API_KEY or PERPLEXITY_API_KEY.startswith("pplx-xxx"):
        print("ERROR: PERPLEXITY_API_KEY not configured")
        print("Run: seokit config")
        return False
    return True
