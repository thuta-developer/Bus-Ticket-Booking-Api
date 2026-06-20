from fastapi import APIRouter
from app.api.v1.endpoints import auth, users

# Main V1 Router
router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
router.include_router(auth.router)
router.include_router(users.router)