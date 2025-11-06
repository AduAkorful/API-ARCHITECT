from fastapi import APIRouter
from app.api.v1.endpoints import services

api_router = APIRouter()
api_router.include_router(services.router, prefix="/services", tags=["Services"])