import os

from scimodels.abstract import APIModel
from scimodels.dependencies import DepedencyLoader

class OpenAIModel(APIModel):
    def __init__(
        self,
        model: str,
        *,
        parallel_count: int | None = 1,
        retries: int | None = 1,
        temperature: float | None = 1.0,
        effort: str | None = None,
        max_tokens: int | None = None
    ):
        self.model = model
        self.temperature = temperature
        self.effort = effort
        self.max_tokens = max_tokens
        self.parallel_count = parallel_count
        self.retries = retries

        # Try to load OpenAI
        dep = DepedencyLoader.load("openai")
        if not dep.loaded:
            raise dep.exception
        self._openai = dep.module

        # Check if OPENAI_API_KEY is set and issue
        # a warning if not
        if not os.getenv("OPENAI_API_KEY"):
            print("SciModels WARNING: your OPENAI_API_KEY enviromental variable is not set. This might cause issues with authentication.")

    def _retrieve_response(
        self,
        query: str
    ) -> str | None:
        request = {
            "model": self.model,
            "messages": [{"role": "user", "content": query}],
            "temperature": self.temperature
        }
        
        if self.effort:
            request["effort"] = self.effort

        if self.max_tokens:
            request["max_tokens"] = self.max_tokens

        response = self._openai.chat.completions.create(**request)

        return response.choices[0].message.content