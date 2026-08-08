from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, roles, permissions, bus_companies, bus,route, schedules, seats,features,bus_images

# Main V1 Router
router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(roles.router)
router.include_router(permissions.router)
router.include_router(bus_companies.router)
router.include_router(bus.router)
router.include_router(route.router)
router.include_router(schedules.router)
router.include_router(seats.router)
router.include_router(features.router)
router.include_router(bus_images.router)
