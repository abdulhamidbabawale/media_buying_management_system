from fastapi import APIRouter, HTTPException
from app.models import Client
from app.database import db


router = APIRouter(prefix="/clients", tags=["Clients"])

@router.post("/", response_model=Client)
async def create_client(client: Client):
    client_dict = client.dict(by_alias=True)  # keep `_id`
    client_dict["_id"] = str(client_dict["_id"])  # force UUID -> string

    await db["clients"].insert_one(client_dict)
    return client

@router.get("/{client_id}", response_model=Client)
async def get_client(client_id: str):
    client = await db["clients"].find_one({"_id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return Client(**client)
