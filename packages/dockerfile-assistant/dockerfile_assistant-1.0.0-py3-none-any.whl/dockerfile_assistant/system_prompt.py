from .config import config
from pathlib import Path

def get_system_prompt() -> str:
    prompts_dir = Path(__file__).parent / "prompts"
    if config.USE_FS_MCP:
        prompt_file = prompts_dir / "fs_mcp_prompt.md"
    else:
        prompt_file = prompts_dir / "default_prompt.md"
    return prompt_file.read_text()
    
system_prompt = get_system_prompt()

def get_dynamic_system_prompt(system_prompt: str) -> str:
    if config.USE_FS_MCP:
        system_prompt = system_prompt.replace("{{OUTPUT_PATH}}", str(config.OUTPUT_PATH))
        system_prompt = system_prompt.replace("{{PROJECT_PATH}}", str(config.PROJECT_PATH))
    return system_prompt

mcp_system_prompt = get_dynamic_system_prompt(system_prompt)