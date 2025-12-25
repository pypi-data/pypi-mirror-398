from mielto.models.base import Model


# TODO: add all supported models
def get_model(model_id: str, model_provider: str) -> Model:
    """Return the right Mielto model instance given a pair of model provider and id"""
    if model_provider == "openai":
        from mielto.models.openai import OpenAIChat

        return OpenAIChat(id=model_id)
    elif model_provider == "anthropic":
        from mielto.models.anthropic import Claude

        return Claude(id=model_id)
    elif model_provider == "gemini":
        from mielto.models.google import Gemini

        return Gemini(id=model_id)
    else:
        raise ValueError(f"Model provider {model_provider} not supported")
