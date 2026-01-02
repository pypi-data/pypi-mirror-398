from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from zenithauth.core.exceptions import InvalidCredentialsError
from zenithauth.core.policy import PasswordPolicy # Import Policy

class SecurityHandler:
    def __init__(self, policy: Optional[PasswordPolicy] = None):
        self.ph = PasswordHasher()
        # Default to a 12-character policy if none provided
        self.policy = policy or PasswordPolicy(min_length=12)

    def hash_password(self, password: str) -> str:
        """Validates policy THEN hashes."""
        self.policy.validate(password) # This raises WeakPasswordError if it fails
        return self.ph.hash(password)

    def verify_password(self, hashed: str, plain: str) -> bool:
        try:
            return self.ph.verify(hashed, plain)
        except VerifyMismatchError:
            raise InvalidCredentialsError("Invalid password.")