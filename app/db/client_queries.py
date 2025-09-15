from uuid import uuid4
from datetime import datetime
from app.db.connection import db
from app.models import Client
from pymongo.errors import PyMongoError
from bson.binary import Binary, UuidRepresentation
from fastapi.encoders import jsonable_encoder

collection = db.clients


async def create_client(client: dict):
    result =await collection.insert_one(client)
    return str(result.inserted_id)

async def get_client_by_id(client_id: str):
    return await collection.find_one({"_id": client_id})

async def list_clients():
    return await collection.find().to_list(100)
