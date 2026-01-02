from typing import Optional, Dict
from zenithauth.core.identity import UserInDB
from zenithauth.protocols.user_repo import UserRepositoryProtocol

class MockUserRepository(UserRepositoryProtocol):
    def __init__(self):
        self.users: Dict[str, UserInDB] = {}

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        return self.users.get(user_id)

    async def save_user(self, user: UserInDB) -> UserInDB:
        self.users[user.id] = user
        return user