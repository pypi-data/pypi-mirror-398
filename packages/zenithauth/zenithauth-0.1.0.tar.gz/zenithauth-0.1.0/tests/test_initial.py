from zenithauth.core.security import SecurityHandler

def test_security_import():
    handler = SecurityHandler()
    hashed = handler.hash_password("secure_password_123")
    assert handler.verify_password(hashed, "secure_password_123") is True