from pydantic_ai.mcp import MCPServerStdio
from .config import config
from pathlib import Path

ALLOWED_TOOLS = [
    "list_directory", 
    "read_file",       
    "write_file",     
]


async def block_dotenv(ctx, call_tool, tool_name: str, args: dict):
    if tool_name in {"read_file","write_file"}:
        path = args.get("path", "")
        if isinstance(path, str) and Path(path).name == ".env":
            return "Access denied"
    return await call_tool(tool_name, args, None)

def get_filesystem_mcp() -> MCPServerStdio | None:
 
    if not config.USE_FS_MCP:
        return None
    
    paths = [str(config.PROJECT_PATH)]
    if config.OUTPUT_PATH != config.PROJECT_PATH:
        paths.append(str(config.OUTPUT_PATH))
    
    fs_server = MCPServerStdio(
        'npx',
        args=[
            '-y',
            '@modelcontextprotocol/server-filesystem',
            *paths,
            
        ],
        process_tool_call=block_dotenv
    )
    
    return fs_server.filtered(lambda _ctx, tool_def: tool_def.name in ALLOWED_TOOLS)


mcp_server = get_filesystem_mcp()