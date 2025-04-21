from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from contextlib import asynccontextmanager
from admin.routes import admin_router
from customer.routes import customer_router
from staff.routes import staff_router
from db.main import init_db, engine
from db.models import SuperAdmin
from config import Config
from utils.helper_func import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession

async def create_super_admin():
    """
    Creates the initial superadmin user. This should only be run once.
    """
    async with engine.begin() as conn:
        async with AsyncSession(bind=conn) as db:
            result = await db.execute(select(SuperAdmin).limit(1))
            if result.scalar_one_or_none():
                print("SuperAdmin already exists.")
                return
            email = Config.ADMIN_EMAIL
            password = Config.ADMIN_PASSWORD
            hashed_password = get_password_hash(password)
            superadmin = SuperAdmin(email=email, password=hashed_password)
            db.add(superadmin)
            await db.commit()
            print("SuperAdmin created.")

@asynccontextmanager
async def life_span(app: FastAPI):
    print(f"Server is starting...")
    await init_db()
    await create_super_admin()
    yield
    print(f"Server has been stopped")

app = FastAPI(
    title="Water Tanker Availability Application",
    version="1.0.0",
    lifespan=life_span,
    description=(
        "This MVP backend provides the necessary APIs and data management for customers to "
        "place orders and for administrators to manage users, drivers, and deliveries manually"
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customer_router, tags=["Customers"])
app.include_router(staff_router, tags=["Drivers"])
app.include_router(admin_router, tags=["Admin"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to the Water Tanker Availability Application API!",
        "project": "Water Tanker Availability Application API",
        "version": app.version,
        "description": app.description,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

