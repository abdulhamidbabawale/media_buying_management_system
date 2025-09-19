from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.jwt import decode_access_token, verify_token_type
from app.db.auth_queries import get_user_by_email
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

class MultiTenantMiddleware:
    """Middleware to enforce client isolation and multi-tenant security"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Skip middleware for auth endpoints and health checks
            if request.url.path.startswith("/api/v1/auth") or request.url.path in ["/", "/api/v1/health"]:
                await self.app(scope, receive, send)
                return
            
            # Extract and validate client context
            try:
                client_id = await self._extract_client_id(request)
                if client_id:
                    # Add client_id to request state for use in endpoints
                    request.state.client_id = client_id
            except HTTPException as e:
                # If client validation fails, return proper JSON response
                response = JSONResponse({"detail": e.detail}, status_code=e.status_code)
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
    
class LoggingMiddleware:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("request")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        client = scope.get("client") or (None, None)
        client_ip = client[0] if client else "-"
        path = scope.get("path")
        method = scope.get("method")

        self.logger.info(f"request start method={method} path={path} ip={client_ip}")

        async def send_wrapper(message):
            if message.get("type") == "http.response.start":
                status_code = message.get("status")
                self.logger.info(f"request end method={method} path={path} status={status_code}")
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            self.logger.exception(f"unhandled error method={method} path={path} error={e}")
            response = JSONResponse({"detail": "Internal Server Error"}, status_code=500)
            await response(scope, receive, send)

    async def _extract_client_id(self, request: Request) -> Optional[str]:
        """Extract client_id from JWT token or request headers"""
        
        # Method 1: Extract from JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_access_token(token)
            if payload and verify_token_type(token, "access"):
                # For now, we'll use user_id as client_id
                # In a real system, you'd have a user-to-client mapping
                return payload.get("user_id")
        
        # Method 2: Extract from custom header (for API keys)
        client_id = request.headers.get("X-Client-ID")
        if client_id:
            return client_id
        
        # Method 3: Extract from query parameters (less secure, for testing)
        client_id = request.query_params.get("client_id")
        if client_id:
            return client_id
        
        raise HTTPException(status_code=401, detail="Client authentication required")

async def get_current_client_id(request: Request) -> str:
    """Dependency to get current client_id from request state"""
    if not hasattr(request.state, 'client_id') or not request.state.client_id:
        raise HTTPException(status_code=401, detail="Client context not found")
    return request.state.client_id

async def verify_client_access(client_id: str, resource_client_id: str):
    """Verify that the requesting client has access to the resource"""
    if client_id != resource_client_id:
        raise HTTPException(
            status_code=403, 
            detail="Access denied: Client does not have permission to access this resource"
        )
    return True

# Client isolation decorator for database queries
def with_client_isolation(func):
    """Decorator to automatically add client_id filter to database queries"""
    async def wrapper(*args, **kwargs):
        # This would be implemented based on your specific query patterns
        # For now, it's a placeholder for the concept
        return await func(*args, **kwargs)
    return wrapper
