import uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, 
                        Numeric, Text, Boolean, Float)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from .main import Base

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    address = Column(Text)
    contact_number = Column(String(20), unique=True)
    registration_date = Column(DateTime(timezone=True), default=func.now())

    orders = relationship("Order", back_populates="customer")
    feedback = relationship("Feedback", back_populates="customer")

class Driver(Base):
    __tablename__ = "drivers"

    driver_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    contact_number = Column(String(20), unique=True, nullable=False)
    vehicle_details = Column(JSONB)
    verification_status = Column(String(50), default="Pending")
    registration_date = Column(DateTime(timezone=True), default=func.now())
    price_per_liter = Column(Float, default=20.0)
    is_active = Column(Boolean, default=True)
    password_hash = Column(String(255))
    
    orders = relationship("Order", back_populates="assigned_driver")

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=False)
    quantity = Column(Numeric, nullable=False)
    location_address = Column(String(200))
    delivery_schedule = Column(DateTime(timezone=True), nullable=False)
    order_date = Column(DateTime(timezone=True), default=func.now())
    delivery_status = Column(String(50), default="Pending")
    assigned_driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.driver_id"), nullable=True)
    payment_status = Column(String(50), default="Pending")
    payment_method = Column(String(50))
    cancellation_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="orders")
    assigned_driver = relationship("Driver", back_populates="orders")
    payments = relationship("Payment", back_populates="order")
    feedback = relationship("Feedback", back_populates="order")

class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False)
    amount = Column(Numeric, nullable=False)
    payment_date = Column(DateTime(timezone=True), default=func.now())
    transaction_id = Column(String(255), unique=True)
    status = Column(String(50))

    order = relationship("Order", back_populates="payments")

class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    feedback_date = Column(DateTime(timezone=True), default=func.now())

    order = relationship("Order", back_populates="feedback")
    customer = relationship("Customer", back_populates="feedback")

class AdminUser(Base):
    __tablename__ = "admin_users"

    admin_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    