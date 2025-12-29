"""
Authentication module for AgentTrace CLI.

Stores tokens securely using the OS keychain (via keyring library).
Falls back to config file on systems without keychain support.
"""
import os
import json
import warnings
from pathlib import Path
from typing import Optional, Dict

# Try to import keyring for secure storage
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    warnings.warn("keyring not installed. Tokens will be stored in plaintext.")

# Constants
SERVICE_NAME = "agenttrace"
CONFIG_DIR = Path.home() / ".agenttrace"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_config() -> Dict:
    """Load configuration from file"""
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def save_config(config: Dict):
    """Save configuration to file"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding='utf-8')


def _migrate_plaintext_token():
    """Migrate token from plaintext config to keyring (one-time)"""
    if not KEYRING_AVAILABLE:
        return
    
    config = get_config()
    plaintext_token = config.get("access_token")
    
    if plaintext_token:
        # Save to keyring
        try:
            keyring.set_password(SERVICE_NAME, "access_token", plaintext_token)
            # Remove from plaintext config
            del config["access_token"]
            config["token_migrated"] = True
            save_config(config)
            print("[AgentTrace] ✅ Token migrated to secure storage")
        except Exception as e:
            warnings.warn(f"Failed to migrate token to keyring: {e}")


def login(token: str):
    """Save access token securely.
    
    Uses OS keychain if available, falls back to config file.
    """
    if KEYRING_AVAILABLE:
        try:
            keyring.set_password(SERVICE_NAME, "access_token", token)
            # Mark as using keyring
            config = get_config()
            if "access_token" in config:
                del config["access_token"]  # Remove plaintext
            config["token_migrated"] = True
            save_config(config)
            return
        except Exception as e:
            warnings.warn(f"Keyring failed, falling back to config: {e}")
    
    # Fallback: plaintext config
    config = get_config()
    config["access_token"] = token
    save_config(config)


def get_token() -> Optional[str]:
    """Get stored access token.
    
    Priority:
    1. AGENTTRACE_TOKEN environment variable (for CI/CD)
    2. OS keychain (encrypted)
    3. Config file (plaintext fallback)
    """
    # CI/CD: Check environment variable first
    env_token = os.environ.get("AGENTTRACE_TOKEN")
    if env_token:
        return env_token
    
    # Migrate plaintext token if needed
    _migrate_plaintext_token()
    
    # Try keyring first
    if KEYRING_AVAILABLE:
        try:
            token = keyring.get_password(SERVICE_NAME, "access_token")
            if token:
                return token
        except Exception:
            pass  # Fall through to config file
    
    # Fallback: plaintext config
    return get_config().get("access_token")


def logout():
    """Remove access token from all storage locations."""
    # Remove from keyring
    if KEYRING_AVAILABLE:
        try:
            keyring.delete_password(SERVICE_NAME, "access_token")
        except Exception:
            pass  # Ignore if not found
    
    # Remove from config file
    config = get_config()
    if "access_token" in config:
        del config["access_token"]
    if "token_migrated" in config:
        del config["token_migrated"]
    save_config(config)


def is_token_secure() -> bool:
    """Check if token is stored securely in keyring."""
    return KEYRING_AVAILABLE and get_config().get("token_migrated", False)

