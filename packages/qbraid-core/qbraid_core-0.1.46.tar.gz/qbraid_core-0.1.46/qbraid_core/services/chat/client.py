# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module providing client for interacting with the qBraid chat service.

"""
from __future__ import annotations

from json import JSONDecodeError
from typing import TYPE_CHECKING, Any, Generator, Literal, Optional, Union

from qbraid_core.client import QbraidClient
from qbraid_core.exceptions import RequestsApiError
from qbraid_core.registry import register_client

from .exceptions import ChatServiceRequestError

if TYPE_CHECKING:
    from requests import Response


@register_client()
class ChatClient(QbraidClient):
    """Client for interacting with qBraid chat service."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        response_format: Optional[Literal["text", "code"]] = None,
    ) -> str:
        """Fetch the full chat response as a dictionary.

        Args:
            prompt (str): The prompt to send to the chat service.
            model (str, optional): The model to use for the chat response.
            response_format (str, optional): The format of the response. Defaults to 'text'.

        Returns:
            str: The complete response as a string.

        Raises:
            ChatServiceRequestError: If the chat request fails.
            ChatServiceRuntimeError: If the chat response cannot be parsed.
        """
        response = self._post_chat_request(prompt, model, response_format, stream=False)

        try:
            response_json = response.json()
            return response_json["content"]
        except (JSONDecodeError, KeyError) as err:
            raise ChatServiceRequestError(f"Failed to parse chat response: {err}") from err

    def chat_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        response_format: Optional[Literal["text", "code"]] = None,
    ) -> Generator[str, None, None]:
        """Stream chat response chunks.

        Args:
            prompt (str): The prompt to send to the chat service.
            model (str, optional): The model to use for the chat response.
            response_format (str, optional): The format of the response. Defaults to 'text'.

        Returns:
            Generator[str, None, None]: A generator that yields chunks of the response.

        Raises:
            ChatServiceRequestError: If the chat request fails.
        """
        response = self._post_chat_request(prompt, model, response_format, stream=True)
        yield from response.iter_content(decode_unicode=True)

    def _post_chat_request(
        self,
        prompt: str,
        model: Optional[str],
        response_format: Optional[Literal["text", "code"]],
        stream: bool,
    ) -> Response:
        """Send a POST request to the chat endpoint with error handling.

        Args:
            prompt (str): The prompt to send to the chat service.
            model (str, optional): The model to use for the chat response.
            response_format (str, optional): The format of the response. Defaults to 'text'.
            stream (bool): Whether the response should be streamed.

        Returns:
            Response: The response object from the POST request.

        Raises:
            ChatServiceRequestError: If the chat request fails.
        """
        response_format = response_format or "text"

        if response_format == "code":
            prompt += " Return only raw code. Do not include any text outside of code blocks."

        payload = {"prompt": prompt, "stream": stream}
        if model:
            payload["model"] = model

        try:
            return self.session.post("/chat", json=payload, stream=stream)
        except RequestsApiError as err:
            raise ChatServiceRequestError(f"Failed to get chat response: {err}") from err

    def get_models(
        self, params: Optional[dict[str, Any]] = None
    ) -> Union[list[dict[str, Any]], dict[str, Any]]:
        """Fetch available models or details of a specific model.

        Args:
            params (dict[str, Any], optional): Optional parameters to filter models.

        Returns:
            list[dict[str, Any]] | dict[str, Any]: A list of models or a specific model.

        Raises:
            ChatServiceRequestError: If the request fails or the model is not found.
        """
        try:
            response = self.session.get("/chat/models", params=params)
            return response.json()
        except RequestsApiError as err:
            raise ChatServiceRequestError(f"Failed to get models: {err}") from err
        except JSONDecodeError as err:
            raise ChatServiceRequestError(f"Failed to parse models: {err}") from err

    def add_model(self, model: str, description: str, pricing: dict[str, float]) -> dict[str, Any]:
        """Add a new chat model to the service.

        Args:
            model (str): The unique identifier for the chat model.
            description (str): A description of the chat model.
            pricing (dict[str, float]): Pricing information with 'input' and 'output' keys.

        Returns:
            dict[str, Any]: The response from the service.

        Raises:
            ChatServiceRequestError: If the request fails.
        """
        payload = {"model": model, "description": description, "pricing": pricing}
        try:
            response = self.session.post("/chat/models", json=payload)
            return response.json()
        except RequestsApiError as err:
            raise ChatServiceRequestError(f"Failed to add model: {err}") from err
        except JSONDecodeError as err:
            raise ChatServiceRequestError(f"Failed to parse add model response: {err}") from err
