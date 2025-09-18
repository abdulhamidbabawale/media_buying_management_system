from fastapi import FastAPI,Depends,status
from app.routers import clients,auth,skus
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Media Buying Management System",dependencies=[Depends(RateLimiter(times=100, seconds=60))])

env= os.getenv("ENVIRONMENT")

# Register routers
app.include_router(clients.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(skus.router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    # Connect to Redis

    redis_url = os.environ.get("REDIS_URL", "redis://redis:6379")
    r = redis.from_url(redis_url, encoding="utf8", decode_responses=True)
    await FastAPILimiter.init(r)

@app.on_event("shutdown")
async def shutdown():
    await FastAPILimiter.close()

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
