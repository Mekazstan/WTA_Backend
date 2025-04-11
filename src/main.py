from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from admin.routes import admin_router
from customer.routes import customer_router
from driver.routes import driver_router
from feedback.routes import feedback_router
from order.routes import order_router
from payment.routes import payment_router
from report.routes import report_router
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

app.include_router(customer_router, prefix="/api/customers", tags=["Customers"])
app.include_router(driver_router, prefix="/api/drivers", tags=["Drivers"])
app.include_router(order_router, prefix="/api/orders", tags=["Orders"])
app.include_router(payment_router, prefix="/api/payments", tags=["Payments"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(report_router, prefix="/api/reports", tags=["Reports"])


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

