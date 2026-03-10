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

    async def authenticate(self, request: Request):

        auth_header = request.headers.get("authorization")

        print("Authorization:", request.headers.get("authorization"))

        if not auth_header:
            raise HTTPException(
                status_code=401,
                headers={
                    "WWW-Authenticate":
                    f'Bearer resource_metadata="{MCP_RESOURCE_URL}/.well-known/oauth-protected-resource/mcp"',
                }
            )

        token = auth_header.replace("Bearer ", "")

        options = TokenValidationOptions(
            issuer=SCALEKIT_ENVIRONMENT_URL,
            audience=[MCP_RESOURCE_URL]
        )

        try:

            claims = scalekit_client.validate_token(
                token,
                options=options
            )

        except Exception as e:

            raise HTTPException(status_code=401, detail=str(e))

        return AccessToken(
            token=token,
            claims=claims,
            scopes=claims.get("scope", "").split(),
            client_id=SCALEKIT_CLIENT_ID
        )

    async def verify_token(self, token: str):
        options = TokenValidationOptions(
            issuer=SCALEKIT_ENVIRONMENT_URL,
            audience=[MCP_RESOURCE_URL]
        )
        
        try:
            claims = scalekit_client.validate_token(
                token,
                options=options
            )
            
            return AccessToken(
                token=token,
                claims=claims,
                scopes=claims.get("scope", "").split(),
                client_id=SCALEKIT_CLIENT_ID
            )
        except Exception as e:
            # Return None to indicate authentication failure
            # The middleware will handle this appropriately
            return None