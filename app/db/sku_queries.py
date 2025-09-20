from uuid import uuid4
from datetime import datetime
from app.db.connection import db
from app.models import SKU
from fastapi.encoders import jsonable_encoder

collection = db.skus

async def create_sku(sku: dict):
    result =await collection.insert_one(sku)
    return str(result.inserted_id)

async def get_sku_list(client_id: str | None = None):
    query = {"client_id": client_id} if client_id else {}
    return await collection.find(query).to_list(100)

async def get_sku_by_id(sku_id: str, client_id: str | None = None):
    query = {"_id": sku_id}
    if client_id:
        query["client_id"] = client_id
    return await collection.find_one(query)

async def update_sku(sku_id: str, sku: dict, client_id: str | None = None):
    query = {"_id": sku_id}
    if client_id:
        query["client_id"] = client_id
    result = await collection.update_one(query, {"$set": sku})
    return result.modified_count
