from fastapi import APIRouter

from . import health, memory

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(memory.router)
