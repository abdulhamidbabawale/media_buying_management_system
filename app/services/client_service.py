from app.models import Client
from fastapi.encoders import jsonable_encoder
from app.db.client_queries import create_client, get_client_by_id, list_clients, update_client
from bson import Binary

async def create_client_service(client: Client):
    client_dict = jsonable_encoder(client)
    try:
        result = await create_client(client_dict)
        if result:
            return {"success": True,
                    "message":"Client Created Successfully",
                    "client_id": str(result)}
        else:
            return {"success": False, "message": "Insertion failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}

async def get_client_by_id_service(client_id: str):
    try:
      client = await get_client_by_id(client_id)
      return client
    except Exception as e:
      return None

async def list_all_clients_service(client_id: str | None = None):
    try:
      clients = await list_clients(client_id)
      return clients
    except Exception as e:
      return {"success": False, "message": str(e)}

async def update_client_service(client_id: str, client: Client):
    client_dict = jsonable_encoder(client)
    try:
        result = await update_client(client_id, client_dict)
        if result:
            return {"success": True,
                    "message":"Client Updated Successfully"}
        else:
            return {"success": False, "message": "Update failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}
