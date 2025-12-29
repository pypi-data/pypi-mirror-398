"""
🏴‍☠️ uzdabrazor - The Anal-King of AI Browser Automation 🏴‍☠️

A beautifully fucked-up browser automation script that gives zero shits about
anything while somehow still working perfectly. Smells like smegma but runs like a dream.

This package provides comprehensive browser automation capabilities with stealth features,
multi-LLM provider support, and organized anarchy throughout the codebase.
"""

__version__ = "1.0.5"
__author__ = "uzdabrazor"
__email__ = "uzdabrazor@example.com"
__description__ = "The Anal-King of AI Browser Automation - A beautifully fucked-up browser automation script that actually works"
__url__ = "https://github.com/uzdabrazor/anal-core"

# Package metadata
__title__ = "uzdabrazor"
__license__ = "MIT"
__copyright__ = "Copyright 2025 uzdabrazor"

# Export main functionality
from .core import main as run_automation
from .cli import main as cli_main

# Package-level constants (simplified to 2 providers)
SUPPORTED_PROVIDERS = [
    "ollama",
    "openrouter",
]

DEFAULT_MODELS = {
    "ollama": "llama3.1",
    "openrouter": "anthropic/claude-3.5-sonnet",
}

# Import core dependencies
import patchright

def get_version() -> str:
    """Get the current version of uzdabrazor."""
    return __version__

def is_stealth_available() -> bool:
    """Check if stealth capabilities (patchright) are available."""
    return True  # Always available since patchright is a core dependency

def get_supported_providers() -> list[str]:
    """Get list of supported LLM providers."""
    return SUPPORTED_PROVIDERS.copy()

def get_default_model(provider: str) -> str:
    """Get the default model for a given provider."""
    return DEFAULT_MODELS.get(provider, "llama3.1")

# Package level constants for configuration (simplified)
CLUSTERFUCK_ENV_DEFAULTS = {
    # LLM provider keys (only the ones we use)
    "OPENROUTER_API_KEY": "",
    "OLLAMA_ENDPOINT": "http://localhost:11434",
    # Browser-use core settings
    "ANONYMIZED_TELEMETRY": "true",
    "BROWSER_USE_CLOUD_SYNC": "",
    "BROWSER_USE_CLOUD_API_URL": "https://api.browser-use.com",
    "BROWSER_USE_CONFIG_DIR": "",
}

# Expose main functions for programmatic usage
__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__description__",
    "__url__",
    "run_automation",
    "cli_main",
    "get_version",
    "is_stealth_available", 
    "get_supported_providers",
    "get_default_model",
    "SUPPORTED_PROVIDERS",
    "DEFAULT_MODELS",
    "CLUSTERFUCK_ENV_DEFAULTS",
]