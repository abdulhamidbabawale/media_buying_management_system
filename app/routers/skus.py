from fastapi import APIRouter, HTTPException
from app.models import SKU
from app.services import sku_service
from app.schemas.sku_schema import SkuUpdateRequest

router = APIRouter(prefix="/skus", tags=["SKU"])

@router.post("/", response_model=dict)
async def create_sku(sku: SKU):
    result = await sku_service.create_sku_service(sku)
    if result.get("success"):
        return {
                 "message": result["message"],
                 "sku_id": result["sku_id"]
               }
    else:
        raise HTTPException(status_code=400, detail=f"Error creating SKU: {result['message']}")

@router.get("/", response_model=dict)
async def get_client_list():
        result = await sku_service.get_sku_list_service()
        if result:
            return {
                 "message": "SKU retrieved successfully",
                 "data": result
               }
        else:
           raise HTTPException(status_code=400, detail=f"Error creating SKU: {result['message']}")

@router.get("/{sku_id}", response_model=dict)
async def get_sku(sku_id: str):
    result = await sku_service.get_sku_by_id_service(sku_id)
    if result:
        return {
                 "message": "SKU retrieved successfully",
                 "data": result
               }
    else:
        raise HTTPException(status_code=404, detail="SKU not found")

@router.put("/{sku_id}", response_model=dict)
async def update_sku(sku_id: str,sku: dict):
    result = await sku_service.update_sku_service(sku_id,sku)
    if result.get("success"):
        return {
                 "message": result["message"]
               }
    else:
        raise HTTPException(status_code=400, detail=f"Error updating SKU: {result['message']}")
