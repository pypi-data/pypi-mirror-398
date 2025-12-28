# fireprompt/prompt.py
# SPDX-License-Identifier: MIT

# imports
import yaml
import inspect

from typing import Any
from typing import Callable
from typing import Optional
from pydantic import BaseModel
from litellm import completion
from jinja2 import Environment
from fireprompt.types import LLM
from fireprompt.logger import Logger
from fireprompt.func import FuncWrapper


class FirePrompt:

    def __init__(
        self,
        func: Callable,
        model: Optional[LLM] = None,
        on_complete: Optional[Callable] = None,
        env: Optional[Environment] = None,
    ) -> None:
        """Initialize FirePrompt class."""
        if not model:
            raise ValueError("model is required")

        self._func = FuncWrapper(func)
        self._logger = Logger.get(self.__class__.__name__)
        self._on_complete = on_complete
        self._model = model
        self._env = env or Environment()

        self._logger.debug("prompt initialized")

    def _parse_func_doc(self) -> dict[str, Any]:
        """Parse function docstring."""
        doc = self._func.doc

        if not doc:
            raise ValueError(
                f"function {self._func.__name__} must have a docstring"
            )

        try:
            parsed = yaml.safe_load(doc)  # load yaml

            if not isinstance(parsed, list):
                # if not a list, raise an error
                raise ValueError("invalid yaml docstring")

            return parsed
        except yaml.YAMLError as e:
            # if not valid yaml, raise an error
            raise ValueError(
                f"invalid yaml docstring: {e}"
            ) from e

    def _get_schema(self) -> dict[str, Any]:
        """Get schema."""
        schema = self._func.return_annotation.model_json_schema()

        schema["additionalProperties"] = False

        if "$defs" in schema:
            for n, s in schema["$defs"].items():
                s["additionalProperties"] = False

        return schema

    def _get_response_format(self) -> dict[str, Any]:
        """Get response format."""
        if not hasattr(
            self._func.return_annotation,
            "model_json_schema"
        ):
            # handle non-Pydantic return types
            return None

        return {
            "type": "json_schema",
            "json_schema": {
                "schema": self._get_schema(),
                "name": self._func.return_annotation.__name__,
                "strict": True
            }
        }

    def _render(self, *args: Any, **kwargs: Any) -> list[dict[str, str]]:
        """Render the prompt."""
        self._logger.debug(f"rendering template for '{self._func.__name__}'")

        messages = []
        for m in self._parse_func_doc():
            messages.append({
                "role": m["role"],
                "content": self._env.from_string(
                    m["content"]
                ).render(
                    **self._func.bind(
                        *args,
                        **kwargs
                    )
                )
            })

        return messages

    def _get_model_config(self) -> dict[str, Any]:
        """Get model config and merge extra params."""
        if not self._model.config:
            return {}

        config = self._model.config.model_dump(exclude_none=True)
        extra = config.pop("extra", {}) or {}
        return {**config, **extra}

    def _parse_response(self, response: Any) -> Any:
        """Parse response."""
        # extract content from response
        content = response.choices[0].message.content

        if (
            self._func.return_annotation
            and self._func.return_annotation != inspect.Signature.empty
            and isinstance(self._func.return_annotation, type)
            and issubclass(self._func.return_annotation, BaseModel)
        ):
            return self._func.return_annotation.model_validate_json(content)

        # return raw response
        return content

    def _call_llm(self, messages: list[dict[str, str]]) -> Any:
        """Call LLM."""
        self._logger.debug(f"model: {self._model.name}")

        response = self._parse_response(
            completion(
                **self._get_model_config(),
                model=self._model.name,
                messages=messages,
                response_format=self._get_response_format()
            )
        )

        self._logger.debug(f"response: {response}")

        return response

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Sync call to the prompt."""
        # call LLM
        response = self._call_llm(
            self._render(
                *args,
                **kwargs
            )
        )

        if self._on_complete:
            # if a callback is provided, call it with the response
            # return the result of the callback
            self._logger.debug("callback exists, executing ...")
            return self._on_complete(response)

        return response
