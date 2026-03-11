from scalekit import ScalekitClient
from scalekit.common.scalekit import TokenValidationOptions

from fastmcp.server.auth import AuthProvider, AccessToken
from fastapi import Request, HTTPException

from config import (
    SCALEKIT_ENVIRONMENT_URL,
    SCALEKIT_CLIENT_ID,
    SCALEKIT_CLIENT_SECRET,
    MCP_RESOURCE_URL
)


scalekit_client = ScalekitClient(
    SCALEKIT_ENVIRONMENT_URL,
    SCALEKIT_CLIENT_ID,
    SCALEKIT_CLIENT_SECRET
)


class ScalekitAuth(AuthProvider):
    """Scalekit authentication provider for MCP server"""

    async def authenticate(self, request: Request):
        """Authenticate incoming requests using Scalekit token validation"""
        auth_header = request.headers.get("authorization")

        print(f"[AUTH] Authorization header: {auth_header}")
        print(f"[AUTH] Request path: {request.url.path}")
        print(f"[AUTH] Request method: {request.method}")

        if not auth_header:
            raise HTTPException(
                status_code=401,
                headers={
                    "WWW-Authenticate":
                    f'Bearer resource_metadata="{MCP_RESOURCE_URL}/.well-known/oauth-protected-resource/mcp"',
                }
            )

        token = auth_header.replace("Bearer ", "")
        
        print(f"[AUTH] Token (first 20 chars): {token[:20]}...")
        print(f"[AUTH] Validating with issuer: {SCALEKIT_ENVIRONMENT_URL}")
        print(f"[AUTH] Validating with audience: {MCP_RESOURCE_URL}")

        options = TokenValidationOptions(
            issuer=SCALEKIT_ENVIRONMENT_URL,
            audience=[MCP_RESOURCE_URL]
        )

        try:
            claims = scalekit_client.validate_token(
                token,
                options=options
            )
            print(f"[AUTH] Token validation successful")
            print(f"[AUTH] Claims: {claims}")
        except Exception as e:
            print(f"[AUTH] Token validation failed: {str(e)}")
            print(f"[AUTH] Exception type: {type(e).__name__}")
            raise HTTPException(status_code=401, detail=str(e))

        return AccessToken(
            token=token,
            claims=claims,
            scopes=claims.get("scope", "").split(),
            client_id=SCALEKIT_CLIENT_ID
        )

    async def verify_token(self, token: str):
        """Verify a token for middleware authentication"""
        print(f"[VERIFY] Verifying token (first 20 chars): {token[:20]}...")
        print(f"[VERIFY] Issuer: {SCALEKIT_ENVIRONMENT_URL}")
        print(f"[VERIFY] Audience: {MCP_RESOURCE_URL}")
        
        options = TokenValidationOptions(
            issuer=SCALEKIT_ENVIRONMENT_URL,
            audience=[MCP_RESOURCE_URL]
        )

        try:
            claims = scalekit_client.validate_token(
                token,
                options=options
            )
            print(f"[VERIFY] Token validation successful")
            print(f"[VERIFY] Claims: {claims}")

            return AccessToken(
                token=token,
                claims=claims,
                scopes=claims.get("scope", "").split(),
                client_id=SCALEKIT_CLIENT_ID
            )
        except Exception as e:
            print(f"[VERIFY] Token validation failed: {str(e)}")
            print(f"[VERIFY] Exception type: {type(e).__name__}")
            # Return None to indicate authentication failure
            # The middleware will handle this appropriately
            return None

# Made with Bob
