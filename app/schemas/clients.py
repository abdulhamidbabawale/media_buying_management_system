from pydantic import BaseModel

class ClientCreateResponse(BaseModel):
    message: str
    client_id: str
