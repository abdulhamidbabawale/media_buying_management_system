from uuid import uuid4
from datetime import datetime
from app.db.connection import db
from app.models import SKU
from fastapi.encoders import jsonable_encoder

collection = db.skus

async def create_sku(sku: dict):
    result =await collection.insert_one(sku)
    return str(result.inserted_id)

async def get_sku_list():
    return await collection.find().to_list(100)

async def get_sku_by_id(sku_id: str):
    return await collection.find_one({"_id": sku_id})

async def update_sku(sku_id: str, sku: dict):
    result = await collection.update_one({"_id": sku_id}, {"$set": sku})
    return result.modified_count
