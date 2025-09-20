from uuid import uuid4
from datetime import datetime
from app.db.connection import db
from app.models import Client
from fastapi.encoders import jsonable_encoder

collection = db.clients


async def create_client(client: dict):
    result =await collection.insert_one(client)
    return str(result.inserted_id)

async def get_client_by_id(client_id: str):
    return await collection.find_one({"_id": client_id})

async def list_clients(client_id: str | None = None):
    query = {"_id": client_id} if client_id else {}
    return await collection.find(query).to_list(100)

async def update_client(client_id: str, client: dict):
    # Only update the matching client document
    result = await collection.update_one({"_id": client_id}, {"$set": client})
    return result.modified_count
