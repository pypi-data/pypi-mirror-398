# fireprompt/func.py
# SPDX-License-Identifier: MIT

# imports
import inspect
import functools

from typing import Any
from typing import Callable
from fireprompt.logger import Logger


class FuncWrapper:

    def __init__(self, func: Callable) -> None:
        """FuncWrapper class."""
        self._func = func
        self._logger = Logger.get(self.__class__.__name__)

        # preserve original function metadata
        functools.update_wrapper(self, func)

    @functools.cached_property
    def signature(self) -> inspect.Signature:
        """Get signature of original function."""
        return inspect.signature(self._func)

    @property
    def return_annotation(self) -> Any:
        """Get return annotation of original function."""
        return self.signature.return_annotation

    @property
    def doc(self) -> str | None:
        """Get docstring of original function."""
        return inspect.getdoc(self._func)

    def bind(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Bind arguments and apply defaults."""
        bound = self.signature.bind(*args, **kwargs)
        bound.apply_defaults()

        return bound.arguments
