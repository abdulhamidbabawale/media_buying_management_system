from fastapi import APIRouter, HTTPException
from app.models import Client
from app.db.connection import db
from app.services import client_service
from app.schemas.clients_schema import ClientCreateResponse,ClientFetchResponse


router = APIRouter(prefix="/clients", tags=["Clients"])

@router.post("/", response_model=ClientCreateResponse)
async def create_client(client: Client):
    result = await client_service.create_client_service(client)
    if result.get("success"):
        return {
                 "message": result["message"],
                 "client_id": result["client_id"]
               }
    else:
        raise HTTPException(status_code=400, detail=f"Error creating client: {result['message']}")

@router.get("/{client_id}", response_model=ClientFetchResponse)
async def get_client(client_id: str):
    client = await client_service.get_client_by_id_service(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message":"Client retrieved successfully","data":client}
