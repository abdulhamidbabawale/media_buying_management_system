from uuid import uuid4
from datetime import datetime
from app.db.connection import db
from app.models import User
from pymongo.errors import PyMongoError
from bson.binary import Binary, UuidRepresentation
from fastapi.encoders import jsonable_encoder
from app.jwt import hash_password, verify_password, create_access_token

collection = db.users


async def create_user(user: dict):
    result = await collection.insert_one(user)
    return str(result.inserted_id)

async def get_user_by_email(email: str):
    return await collection.find_one({"email": email})

async def update_user(email: str, update_data: dict):
    return await collection.update_one({"email": email}, {"$set": update_data})
