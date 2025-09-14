from fastapi import FastAPI
from app.routers import clients

app = FastAPI()


app = FastAPI(title="Media Buying Management System")

# Register routers
app.include_router(clients.router, prefix="/api/v1")

@app.get("/")
def home():
    return {"message": "API is running 🚀"}
