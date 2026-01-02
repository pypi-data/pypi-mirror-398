# ZenithAuth 🛡️

**ZenithAuth** is a professional-grade, high-performance, and secure authentication and authorization library for modern Python applications. It combines the speed of stateless JWTs with the security of stateful Redis-backed revocation.

---

## ✨ Key Features

*   **Secure Hashing:** Powered by **Argon2id**, the industry winner of the Password Hashing Competition.
*   **Hybrid Auth Engine:** Stateless JWTs for speed, paired with a **Redis-backed blacklist** for instant token revocation (logouts).
*   **Modern Data Validation:** Built on **Pydantic V2** for strict type safety and performance.
*   **MFA (Multi-Factor Auth):** Out-of-the-box support for TOTP (Google Authenticator) with built-in QR code generation.
*   **Fine-Grained Authorization:** Role-Based Access Control (RBAC) and scoped permissions support.
*   **FastAPI Native:** Includes first-class Dependency Injection helpers for FastAPI and Starlette.
*   **Agnostic Storage:** Works with any database (SQLAlchemy, Tortoise, MongoDB) via the Repository Protocol.

---

## 🚀 Installation

```bash
pip install zenithauth
```

---

## 🛠️ Quick Start (FastAPI)

ZenithAuth makes protecting your API endpoints intuitive.

```python
from fastapi import FastAPI, Depends
from zenithauth.manager import ZenithAuth
from zenithauth.integrations.fastapi import ZenithAuthFastAPI

app = FastAPI()

# 1. Initialize the library
# Ensure ZENITH_SECRET_KEY and ZENITH_REDIS_URL are in your .env
auth_manager = ZenithAuth()
zenith = ZenithAuthFastAPI(auth_manager)

@app.post("/login")
async def login(email: str, password: str):
    # This handles hashing verification and token generation
    result = await auth_manager.authenticate(email, password)
    return result

@app.get("/secure-data")
async def get_data(user: dict = Depends(zenith.get_current_user)):
    return {"message": f"Hello {user['sub']}, you are authorized!"}

@app.get("/admin-only")
async def admin_portal(user: dict = Depends(zenith.require_role("admin"))):
    return {"message": "Welcome, Administrator."}
```

---

## 🔐 Multi-Factor Authentication (MFA)

Implementing MFA is a two-step flow in ZenithAuth:

### 1. Enrollment
```python
# Generate secret and QR code for the user to scan
setup_data = await auth.mfa_enroll_setup(user_id="123", email="user@example.com")
# setup_data contains: {"secret": "...", "qr_code_base64": "..."}
```

### 2. Verification
```python
# Finalize the login using the 6-digit TOTP code
tokens = await auth.verify_mfa_and_login(user_id="123", code="123456")
```

---

## 🏗️ Architecture

ZenithAuth follows a **Security-by-Default** philosophy:

1.  **Stateless JWTs:** Tokens carry user identity and roles, reducing database hits.
2.  **JTI Tracking:** Every token has a unique ID (JTI).
3.  **Redis Guard:** Upon logout, the JTI is blacklisted in Redis until its natural expiry time, preventing "ghost sessions."
4.  **Entropy-Based Passwords:** We enforce password strength based on character diversity, not just simple length.

---

## 📝 Configuration

ZenithAuth is configured via environment variables for easy deployment:

| Variable | Description | Default |
|----------|-------------|---------|
| `ZENITH_SECRET_KEY` | Secret for JWT signing | **REQUIRED** |
| `ZENITH_REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `ZENITH_ALGORITHM` | JWT Algorithm | `HS256` |
| `ZENITH_MIN_PASSWORD_LENGTH` | Minimum length | `12` |

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.