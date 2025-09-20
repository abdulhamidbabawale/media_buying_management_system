from fastapi import FastAPI,Depends,status, Request
from app.routers import clients,auth,skus,campaigns,metrics,integrations
from app.middleware import MultiTenantMiddleware, LoggingMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
import uvicorn
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Media Buying Management System",dependencies=[Depends(RateLimiter(times=100, seconds=60))])

# Add logging and multi-tenant middleware (order: logging outermost)
app.add_middleware(LoggingMiddleware)
app.add_middleware(MultiTenantMiddleware)

env= os.getenv("ENVIRONMENT", "development")

# Register routers
app.include_router(clients.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(skus.router, prefix="/api/v1")
app.include_router(campaigns.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")
app.include_router(integrations.router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    # Connect to Redis

    if env == "production":
        # inside Docker / Cloud Run
        redis_host = os.getenv("REDIS_HOST")
        redis_port = 6379
    else:
         # local dev
         redis_host = os.getenv("REDIS_HOST", "localhost")
         redis_port = int(os.getenv("REDIS_PORT", 6379))

    r = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
    await FastAPILimiter.init(r)

    # Ensure MongoDB indexes exist
    try:
        from app.db.connection import db
        # Clients
        await db.clients.create_index("_id", unique=True)
        await db.clients.create_index("name")

        # SKUs
        await db.skus.create_index("_id", unique=True)
        await db.skus.create_index("client_id")
        await db.skus.create_index("status")

        # Campaigns
        await db.campaigns.create_index("_id", unique=True)
        await db.campaigns.create_index("client_id")
        await db.campaigns.create_index("sku_id")
        await db.campaigns.create_index("platform")
        await db.campaigns.create_index("status")

        # Performance metrics
        await db.performance_metrics.create_index("campaign_id")
        await db.performance_metrics.create_index("sku_id")
        await db.performance_metrics.create_index("client_id")
        await db.performance_metrics.create_index("timestamp")

        # Integration metrics (new)
        await db.integration_metrics_raw.create_index([("campaign_id", 1), ("vendor", 1), ("start", 1), ("end", 1)])
        await db.integration_metrics.create_index([("campaign_id", 1), ("platform", 1), ("start", 1), ("end", 1)])
    except Exception:
        # Index creation failures should not crash startup, but will be visible in logs
        pass

@app.on_event("shutdown")
async def shutdown():
    await FastAPILimiter.close()

@app.get("/")
async def root():
    return {"message": f"Media Buying Management System API is running 🚀 - {env} environment"}

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        from app.db.connection import db
        await db.command("ping")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    try:
        # Test Redis connection
        import redis.asyncio as redis
        r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379)), db=0, decode_responses=True)
        await r.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy",
        "database": db_status,
        "redis": redis_status,
        "timestamp": datetime.now().isoformat()
    }

