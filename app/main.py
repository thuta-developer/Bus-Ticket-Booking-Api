# app/main.py
from fastapi import FastAPI
from app.core.database import engine, check_db_connection
from app.models.base import Base  # Base model ကို import လုပ်ခြင်းဖြင့် metadata ကို Alembic အတွက် ပြင်ဆင်ပေးတယ်။
from app.api.v1.router import router as v1_router

app = FastAPI(
    title="Bus Ticket System",
    version="1.0.0",
    description="Production Ready Bus Booking API"
)

# ============================================
# Register Routers
# ============================================
app.include_router(v1_router)

# ============================================
# Startup / Shutdown Events
# ============================================


@app.on_event("startup")
async def startup():
    """Application စတင်ချိန်မှာ Database connection ကိုစစ်ဆေးပါ"""
    
    if await check_db_connection():
        print("Database connected")
    else:
        print("Database not connected")
        
    # Production မှာ ဒီနေရာမှာ exit လုပ်သင့်တယ် (သို့မဟုတ် retry)
    # raise RuntimeError("Cannot connect to database")

@app.on_event("shutdown")
async def shutdown():
    """Application ပိတ်ချိန်မှာ Database engine ကိုပိတ်ပါ"""
    await engine.dispose()
    print("Database engine disposed.")
    

@app.get("/health")
async def health_check():
    """Health Check Endpoint"""
    db_status = await check_db_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "service": "bus-ticket-system"
    }
