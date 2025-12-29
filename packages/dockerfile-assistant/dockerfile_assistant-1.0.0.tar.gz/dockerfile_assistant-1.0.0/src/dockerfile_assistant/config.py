import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path.cwd() / ".env")

class config:
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL')
    MODEL_NAME = os.getenv('MODEL_NAME')
    LLM_PROVIDER = os.getenv('LLM_PROVIDER')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY")
    PROJECT_PATH = os.getenv('PROJECT_PATH')
    OUTPUT_PATH = os.getenv('OUTPUT_PATH') or PROJECT_PATH
    USE_FS_MCP = os.getenv("USE_FS_MCP", "false").strip().lower() == "true"

    
    


def validate_config():
    errors = []

    if not config.LLM_PROVIDER:
        errors.append("LLM_PROVIDER is required (Currently supports 'openai','google','anthropic' and 'ollama')")
    if not config.MODEL_NAME:
        errors.append("MODEL_NAME is required")
    if config.LLM_PROVIDER == "openai" and not config.OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is required when using OpenAI")
    if config.LLM_PROVIDER == "google" and not config.GOOGLE_API_KEY:
        errors.append("GOOGLE_API_KEY is required when using Google")  
    if config.LLM_PROVIDER == "anthropic" and not config.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is required when using Anthropic")  
    if config.LLM_PROVIDER == "ollama" and not config.OLLAMA_BASE_URL:
        errors.append("OLLAMA_BASE_URL is required when using Ollama")
    if config.USE_FS_MCP and not config.OUTPUT_PATH:
        errors.append("OUTPUT_PATH is required when using Filesystem MCP")
    if config.USE_FS_MCP and not config.PROJECT_PATH:
        errors.append("PROJECT_PATH is required when using Filesystem MCP")
    if config.PROJECT_PATH and not Path(config.PROJECT_PATH).is_dir():
        errors.append(f"PROJECT_PATH '{config.PROJECT_PATH}' is not a valid directory")
    if config.OUTPUT_PATH and not Path(config.OUTPUT_PATH).is_dir():
        errors.append(f"OUTPUT_PATH '{config.OUTPUT_PATH}' is not a valid directory")

    if errors:
        raise SystemExit("Configuration errors:\n  - " + "\n  - ".join(errors))


validate_config()

