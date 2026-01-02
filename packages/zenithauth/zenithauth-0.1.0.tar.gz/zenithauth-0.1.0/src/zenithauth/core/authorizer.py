from typing import List, Dict, Any, Optional
from zenithauth.core.exceptions import ZenithAuthError

class InsufficientPermissionsError(ZenithAuthError):
    pass

class Authorizer:
    @staticmethod
    def has_role(payload: Dict[str, Any], required_role: str) -> bool:
        """Checks if a specific role exists in the token scopes."""
        scopes = payload.get("scopes", [])
        return required_role in scopes

    @staticmethod
    def has_any_role(payload: Dict[str, Any], roles: List[str]) -> bool:
        """Checks if the user has at least one of the listed roles."""
        scopes = payload.get("scopes", [])
        return any(role in scopes for role in roles)

    @staticmethod
    def validate_ownership(payload: Dict[str, Any], resource_owner_id: str):
        """
        Fine-grained check: Does the token 'sub' match the resource owner?
        Used for: 'Users can only delete THEIR OWN posts'.
        """
        user_id = payload.get("sub")
        if user_id != str(resource_owner_id):
            raise InsufficientPermissionsError("You do not own this resource.")