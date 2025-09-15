from pydantic import BaseModel

class ClientCreateResponse(BaseModel):
    message: str
    client_id: str

"""response for fetching client details"""
class ClientFetchResponse(BaseModel):
    message: str
    data: object
"""response for fetching client details"""
