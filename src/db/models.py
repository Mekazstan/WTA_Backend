from datetime import datetime
from sqlalchemy import (Column, Integer, String, DateTime, 
                        ForeignKey, Enum, Numeric, Boolean)
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .main import Base


class OrderStatus(str, PyEnum):
    PAIRING = "pairing"
    PENDING_PAYMENT = "pending_payment"
    EN_ROUTE = "en_route"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class RecyclableStatus(str, PyEnum):
    PENDING_REVIEW = "pending_review"
    PICKUP_SCHEDULED = "pickup_scheduled"
    DROPPED_OFF = "dropped_off"
    CREDITED = "credited"


class PickupOption(str, PyEnum):
    PICKUP = "pickup"
    DROPOFF = "dropoff"
    
class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    PAID = "paid"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    registration_date = Column(DateTime, default=datetime.utcnow)
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    recyclable_submissions = relationship("RecyclableSubmission", back_populates="customer", cascade="all, delete-orphan")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    customer = relationship("Customer", back_populates="orders")
    destination_address = Column(String, nullable=False)
    water_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PAIRING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    driver = relationship("Driver")
    staff_assigned_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    staff_assigned = relationship("Staff")
    driver_charge = Column(Numeric(10, 2), nullable=True)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_date = Column(DateTime, nullable=True)

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    vehicle_details = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_by_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    created_by = relationship("Staff", remote_side=[id])
    created_at = Column(DateTime, default=datetime.utcnow)

class SuperAdmin(Base):
    __tablename__ = "super_admins"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class RecyclableSubmission(Base):
    __tablename__ = "recyclable_submissions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    customer = relationship("Customer", back_populates="recyclable_submissions")
    image_url = Column(String, nullable=False)
    recyclable_type = Column(String, nullable=False)
    estimated_value = Column(Numeric(10, 2), nullable=True)
    pickup_option = Column(Enum(PickupOption), nullable=False)
    pickup_address = Column(String, nullable=True)
    dropoff_location = Column(String, nullable=True)
    status = Column(Enum(RecyclableStatus), default=RecyclableStatus.PENDING_REVIEW)
    credited_amount = Column(Numeric(10, 2), nullable=True)
    submission_date = Column(DateTime, default=datetime.utcnow)