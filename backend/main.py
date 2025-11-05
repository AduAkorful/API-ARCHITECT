# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# CORRECTED IMPORTS
from backend.app.api.v1.router import api_router
from backend.app.core.config import settings

app = FastAPI(
    title="API Architect Core",
    description="Backend service to generate and deploy microservices.",
    version="0.1.0"
)

# CORS Middleware Setup
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip() for origin in settings.CORS_ORIGINS.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/", tags=["Health Check"])
def read_root():
    """A simple health check endpoint."""
    return {"status": "ok", "message": "API Architect Core is running!"}


# Include the API router
app.include_router(api_router, prefix=settings.API_V1_STR)