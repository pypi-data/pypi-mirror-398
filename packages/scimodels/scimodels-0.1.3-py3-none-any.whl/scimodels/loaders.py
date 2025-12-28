from scimodels.abstract import Model
from scimodels.models import (
    vLLMModel,
    OpenAIModel,
    OpenAIBatchModel,
)

_SUPPORTED_PROVIDERS = {
    "vllm": vLLMModel,
    "openai": OpenAIModel,
    "openai-batch": OpenAIBatchModel,
}

def load_model(
    provider: str,
    model: str,
    *args,
    **kwargs
) -> Model:
    if provider not in _SUPPORTED_PROVIDERS:
        raise ValueError(f"Provider {provider} is not supported.")
    class_ = _SUPPORTED_PROVIDERS[provider]
    model = class_(model, *args, **kwargs)
    model.provider = provider
    return model

def get_providers() -> list[str]:
    return list(_SUPPORTED_PROVIDERS.keys())