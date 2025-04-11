from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from auth.routes import auth_router
from db.main import init_db
from db.mongo import initialize_blocklist

@asynccontextmanager 
async def life_span(app:FastAPI):
    print(f"Server is starting...")
    await init_db()
    await initialize_blocklist()
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
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(auth_router, prefix=f"/api/auth", tags=['auth'])


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

