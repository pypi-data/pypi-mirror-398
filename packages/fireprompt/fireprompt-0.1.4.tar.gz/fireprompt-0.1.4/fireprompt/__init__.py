# fireprompt/__init__.py
# SPDX-License-Identifier: MIT

# imports
import warnings

from fireprompt.types import LLM
from fireprompt.api import prompt
from fireprompt.types import LLMConfig
from fireprompt.types import LLMConfigPreset
from fireprompt.logger import set_debug_mode

# suppress litellm cleanup warnings
warnings.filterwarnings(
    "ignore",
    category=RuntimeWarning,
    message=".*coroutine.*was never awaited.*"
)


# exports public APIs
__all__ = [
    "prompt",
    "LLM",
    "LLMConfig",
    "LLMConfigPreset",
    "enable_logging",
    "disable_logging"
]

# version
__version__ = "0.1.4"


# logging
def enable_logging() -> None:
    """Enable logging."""
    set_debug_mode(True)


def disable_logging() -> None:
    """Disable logging."""
    set_debug_mode(False)
