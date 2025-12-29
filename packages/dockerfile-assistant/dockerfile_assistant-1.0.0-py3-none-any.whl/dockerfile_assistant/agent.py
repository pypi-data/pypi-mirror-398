from pydantic_ai import Agent
from .model import model, model_settings
from .mcp_fs import get_filesystem_mcp
from .system_prompt import system_prompt, mcp_system_prompt
from .config import config

def get_agent_config():
    if not config.USE_FS_MCP:
        return Agent(
            model=model,
            system_prompt=system_prompt,
            model_settings=model_settings,
            retries=5)
    else:
        return Agent(
            model=model,
            system_prompt=mcp_system_prompt,
            toolsets=[get_filesystem_mcp()],
            model_settings=model_settings,
            retries=5)
        
agent = get_agent_config()
        

