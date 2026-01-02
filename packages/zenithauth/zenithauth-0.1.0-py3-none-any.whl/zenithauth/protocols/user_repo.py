from typing import Protocol, Optional, Any
from zenithauth.core.identity import UserInDB

class UserRepositoryProtocol(Protocol):
    """
    Any database adapter must implement these methods.
    This keeps ZenithAuth framework-agnostic.
    """
    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        ...

    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        ...

    async def save_user(self, user: UserInDB) -> UserInDB:
        ...