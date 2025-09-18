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

env= os.getenv("ENVIRONMENT", "development")

# Register routers
app.include_router(clients.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(skus.router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    # Connect to Redis

    if env == "production":
        # inside Docker / Cloud Run
        redis_host = "redis"
        redis_port = 6379
    else:
         # local dev
         redis_host = os.getenv("REDIS_HOST", "localhost")
         redis_port = int(os.getenv("REDIS_PORT", 6379))

    r = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
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
