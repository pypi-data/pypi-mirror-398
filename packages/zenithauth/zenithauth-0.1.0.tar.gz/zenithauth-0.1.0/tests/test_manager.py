import pytest
import os
from zenithauth.manager import ZenithAuth
from zenithauth.core.identity import UserInDB
from .mock_repo import MockUserRepository
from zenithauth.config import ZenithSettings

@pytest.mark.asyncio
async def test_manager_with_settings():
    # 1. Initialize with explicit settings
    settings = ZenithSettings(
        ZENITH_SECRET_KEY="test-key",
        ZENITH_REDIS_URL="redis://redis:6379/0"
    )
    auth = ZenithAuth(settings=settings)
    
    # 2. Test token generation via manager
    tokens = auth.tokens.generate_auth_tokens(user_id="123")
    assert tokens.access_token is not None
    
    # 3. Test decoding
    payload = await auth.authorize(tokens.access_token)
    assert payload["sub"] == "123"

    # 4. Logout
    await auth.logout(tokens.access_token)

    # 5. Verify access is now denied
    from zenithauth.core.exceptions import RevokedTokenError
    with pytest.raises(RevokedTokenError):
        await auth.authorize(tokens.access_token)