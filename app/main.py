from fastapi import FastAPI,Depends,status, Request
from app.routers import clients,auth,skus,campaigns,metrics,google_ads_integrator
from app.middleware import MultiTenantMiddleware, LoggingMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
import uvicorn
import os
from datetime import datetime
from dotenv import load_dotenv
from fastapi.openapi.utils import get_openapi

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
app.include_router(google_ads_integrator.router, prefix="/api/v1")

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


# Expose BearerAuth scheme in OpenAPI so Swagger UI shows the Authorize button
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="API for multi-tenant media buying management with integrations and intelligence.",
        routes=app.routes,
    )
    components = openapi_schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    # Set global security so Swagger UI attaches Authorization header when authorized
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

