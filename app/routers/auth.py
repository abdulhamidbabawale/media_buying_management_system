from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.models import User
from app.schemas.auth_schema import LoginRequest
from app.services.auth_service import register_user,login_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register(user: User):
    result= await register_user(user)
    if result["success"]==True:
        return {"message": "User created successfully",
                "user_id": result["user_id"]}
    else:
        raise HTTPException(status_code=400, detail=f"Error creating user: {result['message']}")



@router.post("/login")
async def login(form_data: LoginRequest):
    result= await login_user(form_data)
    if result["success"]==True:
        return {"access_token": result["access_token"],
                "token_type": result["token_type"]}
    else:
        raise HTTPException(status_code=401, detail=f"Error logging in: {result['message']}")
