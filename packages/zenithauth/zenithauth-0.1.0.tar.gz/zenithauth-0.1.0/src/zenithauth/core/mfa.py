import pyotp
import qrcode
import io
import base64
from qrcode.image.pil import PilImage
from typing import Optional
from zenithauth.core.exceptions import ZenithAuthError

class InvalidMFACodeError(ZenithAuthError):
    pass

class MFAHandler:
    def __init__(self, issuer_name: str = "ZenithAuth"):
        self.issuer_name = issuer_name

    def generate_secret(self) -> str:
        """Generates a random base32 OTP secret."""
        return pyotp.random_base32()

    def get_provisioning_uri(self, email: str, secret: str) -> str:
        """Returns the otpauth:// URI for authenticator apps."""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=email, 
            issuer_name=self.issuer_name
        )

    def verify_code(self, secret: str, code: str) -> bool:
        """Verifies a 6-digit TOTP code."""
        totp = pyotp.totp.TOTP(secret)
        # valid_window=1 allows for 30 seconds of clock drift
        return totp.verify(code, valid_window=1)

    def generate_qr_base64(self, uri: str) -> str:
        """Generates a QR code image as a base64 string for the frontend."""
        # Explicitly use PilImage to ensure compatibility with Pillow
        qr = qrcode.QRCode(image_factory=PilImage)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()