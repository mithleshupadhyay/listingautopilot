from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from prometheus_fastapi_instrumentator import Instrumentator

from listingautopilot.api import assets, designs, generation, health, projects, providers
from listingautopilot.core.config import settings
from listingautopilot.logging import configure_logging, get_logger


load_dotenv()
configure_logging()
logger = get_logger(__name__)
logger.info("Starting %s API version=%s env=%s", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Amazon listing creative pipeline with DB-optional persistence.",
)

# Prometheus metrics must be registered BEFORE startup
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(providers.router)
app.include_router(generation.router)
app.include_router(projects.router)
app.include_router(assets.router)
app.include_router(designs.router)


# Add option to specify JWT token authentication in swagger file
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Apply BearerAuth security globally (to all endpoints)
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
