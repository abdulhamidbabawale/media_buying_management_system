from uuid import uuid4
from datetime import datetime
from app.db.connection import db
from app.models import Client
from pymongo.errors import PyMongoError
from bson.binary import Binary, UuidRepresentation
from fastapi.encoders import jsonable_encoder

collection = db.clients

async def create_client(client: Client):
    client_dict = jsonable_encoder(client)
    try:
        result = await collection.insert_one(client_dict)
        if result.inserted_id:  # Successful insertion
            return {"success": True, "client_id": str(result.inserted_id)}
        else:
            return {"success": False, "error": "Insertion failed"}
    except PyMongoError as e:  # Catch MongoDB errors
        return {"success": False, "error": str(e)}

async def get_client_by_id(client_id: str):
    return await collection.find_one({"_id": client_id})

async def list_clients():
    return await collection.find().to_list(100)
