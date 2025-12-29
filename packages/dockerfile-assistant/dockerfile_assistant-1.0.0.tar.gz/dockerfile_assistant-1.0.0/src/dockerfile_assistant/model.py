from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.settings import ModelSettings
from .config import config
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models import Model


def get_model() -> Model:
    if config.LLM_PROVIDER == "openai":
        return  OpenAIChatModel(
            model_name=config.MODEL_NAME,
            provider=OpenAIProvider(api_key=config.OPENAI_API_KEY)
        )
    elif config.LLM_PROVIDER == "ollama":
        return OpenAIChatModel(
            model_name=config.MODEL_NAME,
            provider=OllamaProvider(base_url=config.OLLAMA_BASE_URL)
        )
    elif config.LLM_PROVIDER == "google":
        return GoogleModel(
            model_name=config.MODEL_NAME,
            provider=GoogleProvider(api_key=config.GOOGLE_API_KEY)
        )
    elif config.LLM_PROVIDER == "anthropic":
        return AnthropicModel(
            model_name=config.MODEL_NAME,
            provider=AnthropicProvider(api_key=config.ANTHROPIC_API_KEY)
        )
    else:
        raise ValueError(f"Unsupported provider: {config.LLM_PROVIDER!r}")

def get_model_settings():
    settings = {
        "temperature": 0.1,
        "top_p": 0.9,
        "max_tokens": 2048,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "timeout": 30.0
    }

    if config.LLM_PROVIDER == "ollama":
        settings["timeout"] = 60.0
    
    return ModelSettings(**settings)


model = get_model()
model_settings = get_model_settings()






