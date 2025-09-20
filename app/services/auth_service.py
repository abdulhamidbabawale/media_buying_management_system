from app.db.auth_queries import get_user_by_email, create_user
# from app.core.security import hash_password
from app.jwt import hash_password, verify_password, create_access_token, create_refresh_token, verify_token_type, decode_access_token
from app.schemas.auth_schema import LoginRequest
from app.models import User
from fastapi.encoders import jsonable_encoder
async def register_user(user_data: User):
    try:
       existing_user = await get_user_by_email(user_data.email)
       if existing_user:
           return {"success": False, "message": "Email already exists"}

       user_dict = jsonable_encoder(user_data)
       user_dict["password"] = hash_password(user_data.password)

       user_id = await create_user(user_dict)
       return {"success": True, "message": "User registered successfully", "user_id": user_id}
    except Exception as e:
       return {"success": False, "message": str(e)}

async def login_user(form_data: LoginRequest):
    user = await get_user_by_email(form_data.email)
    if not user or not verify_password(form_data.password, user["password"]):
        return {"success": False, "message": "Invalid credentials"}

    # Include client_id in token for multi-tenant isolation
    client_id = str(user.get("client_id")) if user.get("client_id") is not None else ""
    token_payload = {
        "sub": user["email"],
        "user_id": str(user["_id"]),
        "client_id": client_id,
        "role": user.get("role", "client"),
    }
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)
    
    return {
        "success": True, 
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

async def refresh_access_token(refresh_token: str):
    """Refresh access token using valid refresh token"""
    try:
        # Verify refresh token is valid and of correct type
        if not verify_token_type(refresh_token, "refresh"):
            return {"success": False, "message": "Invalid refresh token"}
        
        # Decode token to get user info
        payload = decode_access_token(refresh_token)
        if not payload:
            return {"success": False, "message": "Invalid refresh token"}
        
        # Create new access token
        new_access_token = create_access_token({
            "sub": payload["sub"], 
            "user_id": payload["user_id"],
            "client_id": payload.get("client_id", ""),
            "role": payload.get("role", "client"),
        })
        
        return {
            "success": True,
            "access_token": new_access_token
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

