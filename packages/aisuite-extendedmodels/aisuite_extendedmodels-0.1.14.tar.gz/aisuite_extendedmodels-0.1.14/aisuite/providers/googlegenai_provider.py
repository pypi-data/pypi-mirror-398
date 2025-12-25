import os
from typing import List, Dict, Any, Optional, Union, BinaryIO

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from aisuite.provider import Provider, LLMError
from aisuite.framework import ChatCompletionResponse


class GooglegenaiProvider(Provider):
    def __init__(self, **config):
        """
        Initialize the Google GenAI provider with the given configuration.
        """
        if genai is None:
            raise ImportError(
                "The 'google-genai' library is not installed. "
                "Please install it using 'pip install google-genai'."
            )

        # Ensure API key is provided either in config or via environment variable
        api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "Google GenAI API key is missing. Please provide it in the config or set the GEMINI_API_KEY environment variable."
            )

        # Remove api_key from config before passing to Client if it's there
        client_config = config.copy()
        if "api_key" in client_config:
            del client_config["api_key"]

        self.client = genai.Client(api_key=api_key, **client_config)

    def chat_completions_create(self, model, messages, **kwargs):
        """
        Create a chat completion using the Google GenAI SDK.
        """
        try:
            # Extract system instruction if present
            system_instruction = None
            contents = []

            for message in messages:
                role = message.get("role")
                content = message.get("content")
                if role == "system":
                    system_instruction = content
                elif role == "user":
                    contents.append(
                        types.Content(
                            role="user", parts=[types.Part.from_text(text=content)]
                        )
                    )
                elif role == "assistant":
                    contents.append(
                        types.Content(
                            role="model", parts=[types.Part.from_text(text=content)]
                        )
                    )

            # Prepare the generation config
            generate_config = {}
            if system_instruction:
                generate_config["system_instruction"] = system_instruction

            # Merge with kwargs
            if kwargs:
                generate_config.update(kwargs)

            # Call the Google GenAI SDK
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(**generate_config)
                if generate_config
                else None,
            )

            return self._format_response(response)
        except Exception as e:
            raise LLMError(f"An error occurred: {e}")

    def _format_response(self, response) -> ChatCompletionResponse:
        """
        Convert the Google GenAI response to the aisuite ChatCompletionResponse format.
        """
        completion_response = ChatCompletionResponse()

        # Set the content of the first choice
        # response.text can be None or raise an error if blocked
        try:
            if response.text:
                completion_response.choices[0].message.content = response.text
        except Exception:
            # If text is not available (e.g. blocked), we might want to check candidates
            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                if hasattr(part, "text"):
                    completion_response.choices[0].message.content = part.text

        # Set usage if available
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            from aisuite.framework.message import CompletionUsage

            completion_response.usage = CompletionUsage(
                prompt_tokens=response.usage_metadata.prompt_token_count,
                completion_tokens=response.usage_metadata.candidates_token_count,
                total_tokens=response.usage_metadata.total_token_count,
            )

        return completion_response
