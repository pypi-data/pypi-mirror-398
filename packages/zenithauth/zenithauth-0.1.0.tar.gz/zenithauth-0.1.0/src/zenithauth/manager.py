from datetime import timedelta, datetime, timezone
from typing import Optional, Dict, Any, List

from zenithauth.config import ZenithSettings
from zenithauth.core.security import SecurityHandler
from zenithauth.core.tokens import TokenManager, TokenPair
from zenithauth.core.revocation import RevocationStore
from zenithauth.core.authorizer import Authorizer
from zenithauth.core.mfa import MFAHandler, InvalidMFACodeError
from zenithauth.core.logger import logger
from zenithauth.core.exceptions import (
    InvalidCredentialsError, 
    ZenithAuthError, 
    RevokedTokenError,
    InsufficientPermissionsError
)
from zenithauth.protocols.user_repo import UserRepositoryProtocol

class ZenithAuth:
    def __init__(
        self, 
        settings: Optional[ZenithSettings] = None,
        repository: Optional[UserRepositoryProtocol] = None
    ):
        """
        The main entry point for ZenithAuth.
        :param settings: ZenithSettings object. If None, loads from Environment.
        :param repository: A class implementing UserRepositoryProtocol for DB access.
        """
        self.settings = settings or ZenithSettings()
        self.repository = repository
        
        # Core Sub-systems
        self.security = SecurityHandler()
        self.tokens = TokenManager(self.settings)
        self.revocation = RevocationStore(self.settings.REDIS_URL)
        self.authorizer = Authorizer()
        self.mfa = MFAHandler(issuer_name=self.settings.ALGORITHM) # Using algorithm as placeholder or add APP_NAME to config
        
        logger.info("ZenithAuth Manager initialized.")

    # --- AUTHENTICATION FLOW ---

    async def authenticate(self, email: str, password: str) -> dict:
        """
        Step 1: Verify credentials.
        Returns a dict indicating if MFA is required or providing tokens.
        """
        if not self.repository:
            raise ZenithAuthError("Repository not configured.")

        user = await self.repository.get_by_email(email)
        if not user:
            logger.warning(f"Login failed: User {email} not found.")
            raise InvalidCredentialsError("Invalid email or password.")

        # Verify password (Argon2id)
        self.security.verify_password(user.hashed_password, password)

        # Check for MFA
        if user.mfa_enabled:
            logger.info(f"MFA required for user: {email}")
            # Issue a temporary ticket with a restricted scope
            mfa_ticket = self.tokens.create_token(
                subject=user.id,
                expires_delta=timedelta(minutes=5),
                scopes=["mfa_pending"]
            )
            return {
                "mfa_required": True,
                "mfa_ticket": mfa_ticket,
                "user_id": user.id
            }

        # No MFA: Issue full tokens
        tokens = self.tokens.generate_auth_tokens(user.id, scopes=user.roles)
        logger.info(f"User {email} logged in successfully.")
        return {
            "mfa_required": False,
            "tokens": tokens
        }

    async def verify_mfa_and_login(self, user_id: str, code: str) -> TokenPair:
        """
        Step 2: Verify TOTP code after a successful password check.
        """
        user = await self.repository.get_by_id(user_id)
        if not user or not user.mfa_secret:
            raise ZenithAuthError("MFA is not configured for this user.")

        if not self.mfa.verify_code(user.mfa_secret, code):
            logger.warning(f"Invalid MFA code provided for user: {user_id}")
            raise InvalidMFACodeError("The 6-digit code is incorrect or expired.")

        logger.info(f"MFA verified for user: {user_id}")
        return self.tokens.generate_auth_tokens(user.id, scopes=user.roles)

    # --- AUTHORIZATION & GUARDS ---

    async def authorize(self, token: str) -> Dict[str, Any]:
        """
        Validates token signature, expiration, and Redis revocation.
        This is the primary 'Guard' for protected routes.
        """
        payload = self.tokens.decode_token(token)
        
        # Check Redis Blacklist
        if await self.revocation.is_revoked(payload["jti"]):
            logger.warning(f"Revoked token usage attempt: JTI {payload.get('jti')}")
            raise RevokedTokenError("Token has been revoked.")
            
        return payload

    async def authorize_role(self, token: str, required_role: str) -> Dict[str, Any]:
        """Verify token and ensure user has a specific role."""
        payload = await self.authorize(token)
        if not self.authorizer.has_role(payload, required_role):
            raise InsufficientPermissionsError(f"Required role: {required_role}")
        return payload

    async def logout(self, token: str):
        """Immediately invalidates a token by adding its JTI to Redis."""
        payload = self.tokens.decode_token(token)
        await self.revocation.revoke(
            jti=payload["jti"], 
            expires_at=payload["exp"]
        )
        logger.info(f"Token revoked (Logged Out): JTI {payload.get('jti')}")

    # --- MFA ENROLLMENT ---

    async def mfa_enroll_setup(self, user_id: str, email: str) -> dict:
        """
        Generates a new MFA secret and QR code for a user to scan.
        The secret should be saved in 'pending' state until verified.
        """
        secret = self.mfa.generate_secret()
        uri = self.mfa.get_provisioning_uri(email, secret)
        qr_code = self.mfa.generate_qr_base64(uri)
        
        return {
            "secret": secret,
            "qr_code_base64": qr_code,
            "provisioning_uri": uri
        }

    async def mfa_enroll_confirm(self, user_id: str, secret: str, code: str):
        """
        Verifies the first code to finalize MFA enrollment.
        If valid, the user's mfa_enabled should be set to True in the DB.
        """
        if self.mfa.verify_code(secret, code):
            # The library user must now save 'secret' and 'mfa_enabled=True' to their DB
            logger.info(f"MFA Enrollment successful for user: {user_id}")
            return True
        raise InvalidMFACodeError("Initial MFA verification failed.")