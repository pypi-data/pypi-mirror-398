import pytest
import os
from zenithauth.core.tokens import TokenManager
from zenithauth.config import ZenithSettings # Import the new settings class
from zenithauth.core.revocation import RevocationStore

@pytest.mark.asyncio
async def test_token_revocation_flow():
    # 1. Setup using the new Settings object
    settings = ZenithSettings(
        ZENITH_SECRET_KEY="test-secret-key-12345",
        ZENITH_REDIS_URL=os.getenv("REDIS_URL", "redis://redis:6379/0")
    )
    tm = TokenManager(settings)
    store = RevocationStore(settings.REDIS_URL)

    # 2. Create Token
    tokens = tm.generate_auth_tokens(user_id="user_1")
    payload = tm.decode_token(tokens.access_token)
    jti = payload["jti"]

    # 3. Check not revoked
    assert await store.is_revoked(jti) is False

    # 4. Revoke (Logout)
    await store.revoke(jti, payload["exp"])

    # 5. Check revoked
    assert await store.is_revoked(jti) is True