# fireprompt/api.py
# SPDX-License-Identifier: MIT

# imports
import inspect

from typing import Optional
from typing import Callable
from fireprompt.types import LLM
from fireprompt.logger import Logger
from fireprompt.prompt import FirePrompt
from fireprompt.promptasync import FirePromptAsync


# init logger
_logger = Logger.get()


def prompt(
    *,
    model: Optional[LLM] = None,
    on_complete: Optional[Callable] = None
) -> FirePrompt | FirePromptAsync:
    """Prompt decorator."""
    def decorator(func: Callable) -> Callable:
        """Inner decorator function."""
        if not inspect.iscoroutinefunction(func):
            return FirePrompt(
                func=func,
                model=model,
                on_complete=on_complete
            )

        return FirePromptAsync(
            func=func,
            model=model,
            on_complete=on_complete
        )

    return decorator
