from fastapi import FastAPI
from a2a.mcp.schema import MCPTool

def create_mcp_server(tool: MCPTool, handler):
    app = FastAPI(title=f"MCP Tool: {tool.name}")

    @app.get("/.well-known/mcp-tool.json")
    def tool_card():
        return tool.model_dump()

    @app.post("/invoke")
    async def invoke(payload: dict):
        return await handler(payload)

    return app
