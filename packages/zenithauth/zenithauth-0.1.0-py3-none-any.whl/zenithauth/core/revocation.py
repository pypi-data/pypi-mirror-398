import redis.asyncio as redis
from datetime import datetime, timezone
from zenithauth.core.exceptions import RevokedTokenError

class RevocationStore:
    def __init__(self, redis_url: str):
        # Using the async redis client
        self.client = redis.from_url(redis_url, decode_responses=True)

    async def is_revoked(self, jti: str) -> bool:
        """Check if the Token ID exists in the blacklist."""
        return await self.client.exists(f"revoked:{jti}") > 0

    async def revoke(self, jti: str, expires_at: int):
        """
        Add JTI to blacklist. 
        The record expires automatically when the token would have expired.
        """
        now = datetime.now(timezone.utc).timestamp()
        ttl = int(expires_at - now)
        if ttl > 0:
            await self.client.setex(f"revoked:{jti}", ttl, "true")