from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger("middleware")

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # TODO: Implement actual auth verification (e.g. JWT decoding)
        # auth_header = request.headers.get("Authorization")
        # if not auth_header:
        #     return JSONResponse({"error": "Missing Authorization header"}, status_code=401)
        
        response = await call_next(request)
        return response

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )
