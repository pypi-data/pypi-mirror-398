from zenithauth.core.exceptions import ZenithAuthError

class WeakPasswordError(ZenithAuthError):
    pass

class PasswordPolicy:
    def __init__(self, min_length: int = 12, require_non_alpha: bool = True):
        self.min_length = min_length
        self.require_non_alpha = require_non_alpha

    def validate(self, password: str) -> bool:
        if len(password) < self.min_length:
            raise WeakPasswordError(f"Password must be at least {self.min_length} characters.")
        
        if self.require_non_alpha:
            if password.isalpha() or password.isdigit():
                raise WeakPasswordError(
                    "Password is too simple. Use a mix of letters, numbers, or symbols."
                )
        return True