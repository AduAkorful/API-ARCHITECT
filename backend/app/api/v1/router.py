# backend/app/api/v1/router.py

from fastapi import APIRouter
# CORRECTED IMPORT
from backend.app.api.v1.endpoints import services

api_router = APIRouter()

# Include service-related routes
api_router.include_router(services.router, prefix="/services", tags=["Services"])