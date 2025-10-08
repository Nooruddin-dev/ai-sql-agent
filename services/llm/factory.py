from helpers.config import load_config
from services.llm.openai_compatible import OpenAICompatibleService

def make_llm():
    cfg = load_config().llm
    provider = cfg["provider"]
    model = cfg["model"]
    base_url = cfg.get("base_url") or ""
    timeout = cfg.get("timeout_seconds", 60)
    max_retries = cfg.get("max_retries", 0)  # 👈 read from config

    if provider == "openai":
        return OpenAICompatibleService(base_url=None, api_key_env="OPENAI_API_KEY", model=model, timeout=timeout, max_retries = max_retries ,
                                       provider_name = provider)
    if provider == "deepseek":
        return OpenAICompatibleService(base_url=base_url or "https://api.deepseek.com", api_key_env="DEEPSEEK_API_KEY", model=model, timeout=timeout ,max_retries = max_retries ,
                                       provider_name = provider)
    if provider == "gemini-openai":
        return OpenAICompatibleService(base_url=base_url or "https://generativelanguage.googleapis.com/v1beta/openai/", api_key_env="GEMINI_API_KEY", model=model, timeout=timeout, max_retries = max_retries,
                                       provider_name = provider )
    if provider == "ollama":
        return OpenAICompatibleService(base_url=base_url or "http://localhost:11434/v1", api_key_env="OLLAMA_API_KEY", model=model, timeout=timeout, max_retries = max_retries, 
                                       provider_name = provider )
    raise ValueError(f"Unknown provider: {provider}")
