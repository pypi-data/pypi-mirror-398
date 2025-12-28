# fireprompt/promptasync.py
# SPDX-License-Identifier: MIT

# imports
import inspect

from typing import Any
from typing import Callable
from typing import Optional
from jinja2 import Environment
from litellm import acompletion
from fireprompt.types import LLM
from fireprompt.prompt import FirePrompt


class FirePromptAsync(FirePrompt):

    def __init__(
        self,
        func: Callable,
        model: Optional[LLM] = None,
        on_complete: Optional[Callable] = None,
    ) -> None:
        """Initialize FirePromptAsync class."""
        super().__init__(
            func,
            model,
            on_complete,
            env=Environment(
                enable_async=True
            )
        )

        if on_complete:
            if not inspect.iscoroutinefunction(on_complete):
                raise ValueError(
                    "callback must be a coroutine function"
                )

    async def _render(self, *args: Any, **kwargs: Any) -> list[dict[str, str]]:
        """Render the prompt."""
        self._logger.debug(f"rendering template for '{self._func.__name__}'")

        messages = []
        for m in self._parse_func_doc():
            messages.append({
                "role": m["role"],
                "content": await self._env.from_string(
                    m["content"]
                ).render_async(
                    **self._func.bind(
                        *args,
                        **kwargs
                    )
                )
            })

        return messages

    async def _call_llm(self, messages: list[dict[str, str]]) -> Any:
        """Async call LLM."""
        self._logger.debug(f"model: {self._model.name}")

        response = self._parse_response(
            await acompletion(
                **self._get_model_config(),
                model=self._model.name,
                messages=messages,
                response_format=self._get_response_format()
            )
        )

        self._logger.debug(f"response: {response}")

        return response

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Async call to the prompt."""
        # call LLM
        response = await self._call_llm(
            await self._render(
                *args,
                **kwargs
            )
        )

        if self._on_complete:
            self._logger.debug("async callback exists, executing ...")
            return await self._on_complete(response)

        return response
