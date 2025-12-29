from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.modules.example.router import router as example_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(example_router, prefix="/example", tags=["Example"])