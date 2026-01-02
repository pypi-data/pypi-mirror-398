import pytest
import pyotp
from zenithauth.core.mfa import MFAHandler

def test_mfa_flow():
    handler = MFAHandler()
    secret = handler.generate_secret()
    
    # Generate a real code using pyotp (simulating Google Authenticator)
    totp = pyotp.TOTP(secret)
    current_code = totp.now()
    
    # Verify it works
    assert handler.verify_code(secret, current_code) is True
    # Verify wrong code fails
    assert handler.verify_code(secret, "000000") is False

def test_qr_generation():
    handler = MFAHandler()
    secret = handler.generate_secret()
    uri = handler.get_provisioning_uri("test@example.com", secret)
    qr_b64 = handler.generate_qr_base64(uri)
    
    assert isinstance(qr_b64, str)
    assert len(qr_b64) > 100 # Should be a substantial string