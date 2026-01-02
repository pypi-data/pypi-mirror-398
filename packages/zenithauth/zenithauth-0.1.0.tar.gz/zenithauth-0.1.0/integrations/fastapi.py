from typing import Optional, List
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from zenithauth.manager import ZenithAuth
from zenithauth.core.exceptions import ZenithAuthError, RevokedTokenError

class ZenithAuthFastAPI:
    """FastAPI Integration for ZenithAuth."""
    
    def __init__(self, auth_manager: ZenithAuth):
        self.manager = auth_manager
        self.security = HTTPBearer()

    async def get_current_user(
        self, 
        auth: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> dict:
        """
        Dependency that validates the JWT and checks Redis revocation.
        Usage: user = Depends(zenith_fastapi.get_current_user)
        """
        try:
            payload = await self.manager.authorize(auth.credentials)
            return payload
        except RevokedTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )
        except ZenithAuthError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

    def require_role(self, role: str):
        """
        Dependency factory for role-based access.
        Usage: Depends(zenith_fastapi.require_role("admin"))
        """
        async def role_checker(payload: dict = Depends(self.get_current_user)):
            if not self.manager.authorizer.has_role(payload, role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required role: {role}",
                )
            return payload
        return role_checker