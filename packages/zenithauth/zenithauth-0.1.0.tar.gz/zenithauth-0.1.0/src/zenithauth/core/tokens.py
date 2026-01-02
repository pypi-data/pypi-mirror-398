from datetime import datetime, timedelta, timezone
import uuid
from typing import List, Dict, Any
from jose import jwt, JWTError
from zenithauth.config import ZenithSettings  # Import central settings
from zenithauth.core.exceptions import TokenExpiredError, ZenithAuthError

class TokenPair:
    def __init__(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = "bearer"

class TokenManager:
    def __init__(self, settings: ZenithSettings):
        self.settings = settings

    def create_token(self, subject: str, expires_delta: timedelta, scopes: List[str] = []) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {
            "sub": str(subject),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),
            "scopes": scopes
        }
        return jwt.encode(to_encode, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM)

    def generate_auth_tokens(self, user_id: str, scopes: List[str] = []) -> TokenPair:
        access = self.create_token(
            subject=user_id, 
            expires_delta=timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            scopes=scopes
        )
        refresh = self.create_token(
            subject=user_id, 
            expires_delta=timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        return TokenPair(access_token=access, refresh_token=refresh)

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(
                token, 
                self.settings.SECRET_KEY, 
                algorithms=[self.settings.ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired.")
        except JWTError:
            raise ZenithAuthError("Invalid token.")