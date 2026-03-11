from fastapi import FastAPI
from fastmcp import FastMCP
import uvicorn

from scalekit_auth import ScalekitAuth
from tools import register_tools
from config import MCP_RESOURCE_URL, AUTHORIZATION_SERVER


# ---------- MCP SERVER ----------
mcp = FastMCP(
    "Productivity MCP Server",
    auth=ScalekitAuth()
)

register_tools(mcp)

# Create MCP app with trailing slash to prevent redirects
mcp_app = mcp.http_app(path="/")


# ---------- FASTAPI APP ----------
app = FastAPI(lifespan=mcp_app.lifespan)

# Mount at /mcp/ (with trailing slash) to avoid 307 redirects
app.mount("/mcp/", mcp_app)


# ---------- OAuth Metadata ----------
# OAuth metadata endpoint - must be accessible without /mcp prefix
@app.get("/.well-known/oauth-protected-resource/mcp")
async def oauth_metadata():
    return {
        "authorization_servers": [
            AUTHORIZATION_SERVER
        ],
        "bearer_methods_supported": ["header"],
        "resource": MCP_RESOURCE_URL,
        "resource_documentation": f"{MCP_RESOURCE_URL}/docs",
        "scopes_supported": [
            "profile:read",
            "analytics:read"
        ]
    }


# ---------- Run Server ----------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        reload=False,  # Disable reload to prevent session termination
        log_level="info"
    )

# Made with Bob
