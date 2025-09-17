from app.models import SKU
from fastapi.encoders import jsonable_encoder
from app.db.sku_queries import create_sku,get_sku_list,get_sku_by_id,update_sku

async def create_sku_service(sku: SKU):
    sku_dict = jsonable_encoder(sku)
    try:
        result = await create_sku(sku_dict)
        if result:
            return {"success": True,
                    "message":"SKU Created Successfully",
                    "sku_id": str(result)}
        else:
            return {"success": False, "message": "Insertion failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}

async def get_sku_list_service():
    try:
      skus = await get_sku_list()
      return skus
    except Exception as e:
      return {"success": False, "message": str(e)}

async def get_sku_by_id_service(sku_id: str):
    try:
      sku = await get_sku_by_id(sku_id)
      return sku
    except Exception as e:
      return None

async def update_sku_service(sku_id: str, sku: SKU):
    sku_dict = jsonable_encoder(sku)
    try:
        result = await update_sku(sku_id, sku_dict)
        if result:
            return {"success": True,
                    "message":"SKU Updated Successfully",
                    "sku_id": str(sku_id)}
        else:
            return {"success": False, "message": "Update failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}
