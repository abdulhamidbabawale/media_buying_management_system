from fastapi import APIRouter, HTTPException, Depends, Request
from app.models import Client
from app.services import client_service
from app.schemas.clients_schema import ClientCreateResponse,ClientFetchResponse
from app.middleware import (
    get_current_client_id,
    get_current_client_id_optional,
    get_current_client_id_or_admin,
    get_current_user_role,
    verify_client_access,
)


router = APIRouter(prefix="/clients", tags=["Clients"])

@router.post("/", response_model=ClientCreateResponse)
async def create_client(client: Client, request: Request, client_id: str = Depends(get_current_client_id_or_admin)):
    result = await client_service.create_client_service(client)
    if result.get("success"):
        return {
                 "message": result["message"],
                 "client_id": result["client_id"]
               }
    else:
        raise HTTPException(status_code=400, detail=f"Error creating client: {result['message']}")

@router.get("/", response_model=ClientFetchResponse)
async def get_client_list(request: Request, role: str = Depends(get_current_user_role), current_client_id = Depends(get_current_client_id_optional)):
    # Admin can view all; client sees only own record
    if role == "admin":
        clients = await client_service.list_all_clients_service()
        return {"message":"Client retrieved successfully","data":clients}
    if current_client_id:
        client = await client_service.get_client_by_id_service(current_client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return {"message":"Client retrieved successfully","data":[client]}
    raise HTTPException(status_code=401, detail="Client context not found")


@router.get("/{client_id}", response_model=ClientFetchResponse)
async def get_client(client_id: str, request: Request, current_client_id = Depends(get_current_client_id_optional)):
    await verify_client_access(current_client_id, client_id, request)
    client = await client_service.get_client_by_id_service(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message":"Client retrieved successfully","data":client}


@router.put("/{client_id}", response_model=dict)
async def update_client(client_id: str, client: dict, request: Request, current_client_id = Depends(get_current_client_id_optional)):
    await verify_client_access(current_client_id, client_id, request)
    result = await client_service.update_client_service(client_id,client)
    if result.get("success"):
        return {
                 "message": result["message"]
               }
    else:
        raise HTTPException(status_code=400, detail=f"Error updating client: {result['message']}")
