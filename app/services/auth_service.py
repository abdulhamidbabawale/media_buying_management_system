from app.db.auth_queries import get_user_by_email, create_user
# from app.core.security import hash_password
from app.jwt import hash_password, verify_password, create_access_token
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

    token = create_access_token({"sub": user["email"]})
    return {"success": True, "access_token": token, "token_type": "bearer"}

