from fastapi import FastAPI
from src.config import Settings
from src.providers.factory import ProviderFactory
from src.middleware import AuthMiddleware, global_exception_handler
from src.api.openai import routes as openai_routes
from src.api.middesk import routes as middesk_routes
from src.api.dome import routes as dome_routes

def create_app() -> FastAPI:
    settings = Settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Auto-generated connector service",
        # OpenAPI documentation endpoints (enabled by default)
        docs_url="/docs",           # Swagger UI
        redoc_url="/redoc",         # ReDoc UI
        openapi_url="/openapi.json" # OpenAPI spec
    )

    # Initialize Context (Singleton)
    factory = ProviderFactory(settings)
    app.state.context = factory.create_context()

    # Middleware
    app.add_middleware(AuthMiddleware)
    app.add_exception_handler(Exception, global_exception_handler)

    # Health Check
    @app.get("/health")
    def health_check():
        return {
            "status": "ok", 
            "version": settings.APP_VERSION,
            "providers": ["openai", "middesk", "dome"]
        }

    # Register Routers
    app.include_router(openai_routes.router)
    app.include_router(middesk_routes.router)
    app.include_router(dome_routes.router)

    return app
