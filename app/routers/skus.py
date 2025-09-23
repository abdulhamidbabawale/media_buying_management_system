from fastapi import APIRouter, HTTPException, Depends, Request
from app.models import SKU
from app.services import sku_service
from app.schemas.sku_schema import SkuUpdateRequest
from app.middleware import (
    get_current_client_id,
    get_current_client_id_optional,
    get_current_user_role,
    verify_client_access,
)

router = APIRouter(prefix="/skus", tags=["SKU"])

@router.post("/", response_model=dict)
async def create_sku(sku: SKU, request: Request, client_id: str = Depends(get_current_client_id)):
    # Enforce that SKU belongs to the authenticated client
    await verify_client_access(client_id, sku.client_id, request)
    result = await sku_service.create_sku_service(sku)
    if result.get("success"):
        return {
                 "message": result["message"],
                 "sku_id": result["sku_id"]
               }
    else:
        raise HTTPException(status_code=400, detail=f"Error creating SKU: {result['message']}")

@router.get("/", response_model=dict)
async def get_client_list(
    request: Request,
    role: str = Depends(get_current_user_role),
    current_client_id = Depends(get_current_client_id_optional),
):
        # Admin can view all SKUs (no client filter). Clients see only their own.
        if role == "admin":
            result = await sku_service.get_sku_list_service(None)
        else:
            if not current_client_id:
                raise HTTPException(status_code=401, detail="Client context not found")
            result = await sku_service.get_sku_list_service(current_client_id)

        # Treat empty list as a valid response
        if result is None:
            return {"message": "SKU retrieved successfully", "data": []}
        return {"message": "SKU retrieved successfully", "data": result}

@router.get("/{sku_id}", response_model=dict)
async def get_sku(
    sku_id: str,
    request: Request,
    role: str = Depends(get_current_user_role),
    current_client_id = Depends(get_current_client_id_optional),
):
    # Admin bypasses client filter by passing None
    effective_client_id = None if role == "admin" else current_client_id
    if role != "admin" and not current_client_id:
        raise HTTPException(status_code=401, detail="Client context not found")
    result = await sku_service.get_sku_by_id_service(sku_id, effective_client_id)
    if result:
        return {
                 "message": "SKU retrieved successfully",
                 "data": result
               }
    else:
        raise HTTPException(status_code=404, detail="SKU not found")

@router.put("/{sku_id}", response_model=dict)
async def update_sku(
    sku_id: str,
    sku: dict,
    request: Request,
    role: str = Depends(get_current_user_role),
    current_client_id = Depends(get_current_client_id_optional),
):
    # Admin bypass: can update any SKU; clients restricted to their own
    effective_client_id = None if role == "admin" else current_client_id
    if role != "admin" and not current_client_id:
        raise HTTPException(status_code=401, detail="Client context not found")
    existing = await sku_service.get_sku_by_id_service(sku_id, effective_client_id)
    if not existing:
        raise HTTPException(status_code=404, detail="SKU not found")
    result = await sku_service.update_sku_service(sku_id, sku, effective_client_id)
    if result.get("success"):
        return {
                 "message": result["message"]
               }
    else:
        raise HTTPException(status_code=400, detail=f"Error updating SKU: {result['message']}")
