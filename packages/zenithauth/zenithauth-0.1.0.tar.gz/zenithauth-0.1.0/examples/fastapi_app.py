from fastapi import FastAPI, Depends
from zenithauth.manager import ZenithAuth
from zenithauth.integrations.fastapi import ZenithAuthFastAPI

app = FastAPI()

# 1. Initialize the library
auth_manager = ZenithAuth(
    secret_key="SUPER_SECRET_KEY", 
    redis_url="redis://localhost:6379/0"
)
# 2. Initialize the FastAPI integration
zenith = ZenithAuthFastAPI(auth_manager)

@app.get("/public")
def public_route():
    return {"message": "Welcome to the public area!"}

@app.get("/secure")
def secure_route(user: dict = Depends(zenith.get_current_user)):
    return {"message": f"Hello User {user['sub']}, you are authorized!"}

@app.get("/admin")
def admin_route(user: dict = Depends(zenith.require_role("admin"))):
    return {"message": "Hello Admin, you have access to the dashboard!"}