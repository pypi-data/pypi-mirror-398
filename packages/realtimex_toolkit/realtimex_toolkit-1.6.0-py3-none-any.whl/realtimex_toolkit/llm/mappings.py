"""LLM provider credential mappings for LiteLLM compatibility."""

PROVIDER_CREDENTIAL_MAPPINGS: dict[str, list[tuple[str, str, bool]]] = {
    "openai": [
        ("OPEN_AI_KEY", "OPENAI_API_KEY", True),
    ],
    "anthropic": [
        ("ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY", True),
    ],
    "azure": [
        ("AZURE_OPENAI_KEY", "AZURE_OPENAI_API_KEY", True),
        ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_ENDPOINT", True),
    ],
    "gemini": [
        ("GEMINI_API_KEY", "GEMINI_API_KEY", True),
    ],
    "realtimexai": [
        ("REALTIMEX_AI_API_KEY", "OPENAI_API_KEY", True),
        ("REALTIMEX_AI_BASE_PATH", "OPENAI_API_BASE", True),
    ],
    "ollama": [
        ("OLLAMA_BASE_PATH", "OPENAI_API_BASE", True),
    ],
    "groq": [
        ("GROQ_API_KEY", "GROQ_API_KEY", True),
    ],
    "cohere": [
        ("COHERE_API_KEY", "COHERE_API_KEY", True),
    ],
    "mistral": [
        ("MISTRAL_API_KEY", "MISTRAL_API_KEY", True),
    ],
    "perplexity": [
        ("PERPLEXITY_API_KEY", "PERPLEXITYAI_API_KEY", True),
    ],
    "openrouter": [
        ("OPENROUTER_API_KEY", "OPENROUTER_API_KEY", True),
    ],
    "togetherai": [
        ("TOGETHER_AI_API_KEY", "TOGETHERAI_API_KEY", True),
    ],
    "fireworksai": [
        ("FIREWORKS_AI_LLM_API_KEY", "FIREWORKS_API_KEY", True),
    ],
    "deepseek": [
        ("DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY", True),
    ],
    "xai": [
        ("XAI_LLM_API_KEY", "XAI_API_KEY", True),
    ],
    "novita": [
        ("NOVITA_LLM_API_KEY", "NOVITA_API_KEY", True),
    ],
    "bedrock": [
        ("AWS_BEDROCK_LLM_ACCESS_KEY_ID", "AWS_ACCESS_KEY_ID", True),
        ("AWS_BEDROCK_LLM_ACCESS_KEY", "AWS_SECRET_ACCESS_KEY", True),
        ("AWS_BEDROCK_LLM_REGION", "AWS_REGION_NAME", True),
    ],
    "localai": [
        ("LOCAL_AI_BASE_PATH", "OPENAI_API_BASE", True),
        ("LOCAL_AI_API_KEY", "OPENAI_API_KEY", False),
    ],
    "lmstudio": [
        ("LMSTUDIO_BASE_PATH", "OPENAI_API_BASE", True),
    ],
    "textgenwebui": [
        ("TEXT_GEN_WEB_UI_BASE_PATH", "OPENAI_API_BASE", True),
        ("TEXT_GEN_WEB_UI_API_KEY", "OPENAI_API_KEY", False),
    ],
    "koboldcpp": [
        ("KOBOLD_CPP_BASE_PATH", "OPENAI_API_BASE", True),
    ],
    "litellm": [
        ("LITE_LLM_BASE_PATH", "OPENAI_API_BASE", True),
        ("LITE_LLM_API_KEY", "OPENAI_API_KEY", False),
    ],
    "generic-openai": [
        ("GENERIC_OPEN_AI_BASE_PATH", "OPENAI_API_BASE", True),
        ("GENERIC_OPEN_AI_API_KEY", "OPENAI_API_KEY", True),
    ],
    "nvidia-nim": [
        ("NVIDIA_NIM_LLM_BASE_PATH", "OPENAI_API_BASE", True),
    ],
    "huggingface": [
        ("HUGGING_FACE_LLM_API_KEY", "HUGGINGFACE_API_KEY", True),
        ("HUGGING_FACE_LLM_ENDPOINT", "OPENAI_API_BASE", True),
    ],
    "dpais": [
        ("DPAIS_LLM_BASE_PATH", "OPENAI_API_BASE", True),
    ],
    "apipie": [
        ("APIPIE_LLM_API_KEY", "APIPIE_API_KEY", True),
    ],
    "ppio": [
        ("PPIO_API_KEY", "PPIO_API_KEY", True),
    ],
}
