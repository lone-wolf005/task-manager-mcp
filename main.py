from fastapi import FastAPI
from fastmcp import FastMCP
import uvicorn


from scalekit_auth import ScalekitAuth
from tools import register_tools
from config import MCP_RESOURCE_URL, AUTHORIZATION_SERVER

mcp = FastMCP(
    "Productivity MCP Server",
    auth=ScalekitAuth()
)

register_tools(mcp)

mcp_app = mcp.http_app()

app = FastAPI(
    lifespan=mcp_app.lifespan,
    redirect_slashes=False
)

app.mount("/mcp", mcp_app)


@app.get("/.well-known/oauth-protected-resource/mcp")
async def oauth_metadata():

    return {
        "authorization_servers": [
            AUTHORIZATION_SERVER
        ],
        "bearer_methods_supported": ["header"],
        "resource": f"{MCP_RESOURCE_URL}/mcp",
        "resource_documentation": f"{MCP_RESOURCE_URL}/docs",
        "scopes_supported": [
            "profile:read",
            "analytics:read"
        ]
    }
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
    )