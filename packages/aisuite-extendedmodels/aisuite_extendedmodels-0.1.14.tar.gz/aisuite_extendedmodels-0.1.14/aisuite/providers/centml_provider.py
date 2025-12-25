import os
import openai
from aisuite.provider import Provider

class CentmlProvider(Provider):
    def __init__(self, **config):
        """
        CentML is OpenAI-compatible. We just point the OpenAI client 
        to the CentML base URL.
        """
        api_key = config.get("api_key") or os.getenv("CENTML_API_KEY")
        if not api_key:
            raise ValueError("CentML API key is missing.")

        # CentML uses the standard /v1 path
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.centml.com/openai/v1"
        )

    def chat_completions_create(self, model, messages, **kwargs):
        # We don't need to normalize! 
        # aisuite expects an object that looks like an OpenAI response.
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )