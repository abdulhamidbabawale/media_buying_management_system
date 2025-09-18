from fastapi import FastAPI,Depends,status
from app.routers import clients,auth,skus
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Media Buying Management System")

env= os.getenv("ENVIRONMENT")

# Register routers
app.include_router(clients.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(skus.router, prefix="/api/v1")



@app.get("/")
def home():
    # env= os.getenv("ENVIRONMENT")
    return {"message": f"API is running 🚀 this is {env} environment"}

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Simple health check endpoint.
    Returns OK if the API is running.
    """
    return {"status": "ok", "message": "API is healthy 🚀"}
