# FastAPI Endpoints (Organized as in the flow)
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, security
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import timedelta

app = FastAPI()

# Security Setup (JWT and Password Hashing)
SECRET_KEY = "your_secret_key"  #  Use a strong, random key from environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")  #  For login endpoint


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Error Handling
def raise_http_exception(status_code: int, detail: str):
    raise HTTPException(status_code=status_code, detail=detail)

# --- Authentication and Authorization ---

# 1. Customer Registration
@app.post("/api/customers/register/", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def register_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    db_customer = db.query(Customer).filter(Customer.email == customer.email).first()
    if db_customer:
        raise_http_exception(status.HTTP_400_BAD_REQUEST, "Email already registered")
    hashed_password = get_password_hash(customer.password)
    db_customer = Customer(
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        password=hashed_password,
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

# 5. Customer Login
@app.post("/api/customers/login/")
def login_customer(form_data: security.OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_customer = db.query(Customer).filter(Customer.email == form_data.username).first()
    if not db_customer or not verify_password(form_data.password, db_customer.password):
        raise_http_exception(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    access_token_data = {"sub": str(db_customer.id), "user_type": "customer"} # added user_type
    access_token = create_access_token(access_token_data)
    return {"access_token": access_token, "token_type": "bearer"}

# 6. Customer Password Reset Request
@app.post("/api/customers/password/reset/request/")
def request_customer_password_reset(email: EmailStr, db: Session = Depends(get_db)):
    db_customer = db.query(Customer).filter(Customer.email == email).first()
    if not db_customer:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Email not found")
    #  Send email with reset link (implementation depends on your email service)
    #  The reset link should contain a token (e.g., a short-lived JWT)
    print(f"Reset link sent to {email}") # Replace with actual email sending
    return {"message": "Password reset link sent to your email"}

# 6. Customer Password Reset Confirm
@app.post("/api/customers/password/reset/confirm/")
def confirm_customer_password_reset(new_password: str, confirm_new_password: str, token: str, db: Session = Depends(get_db)):
    if new_password != confirm_new_password:
        raise_http_exception(status.HTTP_400_BAD_REQUEST, "Passwords do not match")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) #  validate the token
        user_id = payload.get("sub")
        user_type = payload.get("user_type") # check the user_type
        if user_type != 'customer':
            raise_http_exception(status.HTTP_400_BAD_REQUEST, "Invalid Token")
    except JWTError:
        raise_http_exception(status.HTTP_400_BAD_REQUEST, "Invalid token")
    db_customer = db.query(Customer).filter(Customer.id == user_id).first()
    if not db_customer:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "User not found")
    hashed_password = get_password_hash(new_password)
    db_customer.password = hashed_password
    db.commit()
    return {"message": "Password reset successfully"}

# --- Helper function to get current user ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user_type = payload.get("user_type") # check user type
        if user_id is None or user_type is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    if user_type == "customer":
        user = db.query(Customer).filter(Customer.id == user_id).first()
    elif user_type == "staff":
        user = db.query(Staff).filter(Staff.id == user_id).first()
    elif user_type == "superadmin":
        user = db.query(SuperAdmin).filter(SuperAdmin.id == user_id).first()
    else:
        raise credentials_exception

    if user is None:
        raise credentials_exception
    return user

# --- Customer Endpoints ---

# 2. Customer Create Order
@app.post("/api/customers/orders/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, current_customer: Customer = Depends(get_current_user), db: Session = Depends(get_db)):
    if not isinstance(current_customer, Customer):
        raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only create orders.")
    db_order = Order(
        customer_id=current_customer.id,
        destination_address=order.destination_address,
        water_amount=order.water_amount,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

# 4. Customer Review Previous Orders
@app.get("/api/customers/orders/", response_model=List[OrderRead])
def get_customer_orders(current_customer: Customer = Depends(get_current_user), db: Session = Depends(get_db)):
    if not isinstance(current_customer, Customer):
        raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only view their own orders.")
    orders = db.query(Order).filter(Order.customer_id == current_customer.id).all()
    return orders

#  Get a Single Order
@app.get("/api/customers/orders/{order_id}/", response_model=OrderRead)
def get_customer_order(order_id: int, current_customer: Customer = Depends(get_current_user), db: Session = Depends(get_db)):
    if not isinstance(current_customer, Customer):
        raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only view their own order.")
    order = db.query(Order).filter(Order.id == order_id, Order.customer_id == current_customer.id).first()
    if not order:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    return order

# 3. Customer Cancel Order
@app.patch("/api/customers/orders/{order_id}/cancel/", response_model=OrderRead)
def cancel_order(order_id: int, current_customer: Customer = Depends(get_current_user), db: Session = Depends(get_db)):
    if not isinstance(current_customer, Customer):
        raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only cancel their own orders.")
    db_order = db.query(Order).filter(Order.id == order_id, Order.customer_id == current_customer.id).first()
    if not db_order:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    if db_order.status != OrderStatus.PAIRING:
        raise_http_exception(status.HTTP_400_BAD_REQUEST, "Order cannot be cancelled at this status")
    db_order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(db_order)
    return db_order

# 7. Customer Upload Recyclable
@app.post("/api/customers/recyclables/", response_model=RecyclableSubmissionRead, status_code=status.HTTP_201_CREATED)
def create_recyclable_submission(
    submission: RecyclableSubmissionCreate,
    current_customer: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not isinstance(current_customer, Customer):
        raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only create recyclable submissions.")

    db_submission = RecyclableSubmission(
        customer_id=current_customer.id,
        image_url=submission.image_url,
        recyclable_type=submission.recyclable_type,
        pickup_option=submission.pickup_option,
        pickup_address=submission.pickup_address,
        dropoff_location=submission.dropoff_location,
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission

# Get Customer Recyclable Submissions
@app.get("/api/customers/recyclables/", response_model=List[RecyclableSubmissionRead])
def get_customer_recyclable_submissions(
    current_customer: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not isinstance(current_customer, Customer):
        raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only view their own recyclable submissions.")
    submissions = db.query(RecyclableSubmission).filter(RecyclableSubmission.customer_id == current_customer.id).all()
    return submissions

# Get a Customer Recyclable Submission
@app.get("/api/customers/recyclables/{submission_id}/", response_model=RecyclableSubmissionRead)
def get_customer_recyclable_submission(
    submission_id: int,
    current_customer: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not isinstance(current_customer, Customer):
        raise_http_exception(status.HTTP_403_FORBIDDEN, "Customers can only view their own recyclable submission.")
    submission = (
        db.query(RecyclableSubmission)
        .filter(RecyclableSubmission.id == submission_id, RecyclableSubmission.customer_id == current_customer.id)
        .first()
    )
    if not submission:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Recyclable submission not found")
    return submission

# --- Staff/Admin Authentication ---
#Staff Login
@app.post("/api/admin/login/")
def login_staff(form_data: security.OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_staff = db.query(Staff).filter(Staff.email == form_data.username).first()
    if not db_staff or not verify_password(form_data.password, db_staff.password):
        db_superadmin = db.query(SuperAdmin).filter(SuperAdmin.email == form_data.username).first()
        if not db_superadmin or not verify_password(form_data.password, db_superadmin.password):
            raise_http_exception(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
        else:
             access_token_data = {"sub": str(db_superadmin.id), "user_type": "superadmin"}
             access_token = create_access_token(access_token_data)
             return {"access_token": access_token, "token_type": "bearer", "user_type": "superadmin"}

    access_token_data = {"sub": str(db_staff.id), "user_type": "staff"} # added user_type
    access_token = create_access_token(access_token_data)
    return {"access_token": access_token, "token_type": "bearer", "user_type": "staff"}

# Staff/SuperAdmin Password Reset Request
@app.post("/api/admin/password/reset/request/")
def request_staff_password_reset(email: EmailStr, db: Session = Depends(get_db)):
    db_staff = db.query(Staff).filter(Staff.email == email).first()
    if not db_staff:
        db_superadmin = db.query(SuperAdmin).filter(SuperAdmin.email == email).first()
        if not db_superadmin:
            raise_http_exception(status.HTTP_404_NOT_FOUND, "Email not found")
        else:
             #  Send email with reset link (implementation depends on your email service)
             #  The reset link should contain a token
            print(f"Super Admin Reset link sent to {email}")
            return {"message": "Password reset link sent to your email"}
    #  Send email with reset link (implementation depends on your email service)
    #  The reset link should contain a token
    print(f"Staff Reset link sent to {email}") # Replace with actual email sending
    return {"message": "Password reset link sent to your email"}

# Staff/SuperAdmin Password Reset Confirm
@app.post("/api/admin/password/reset/confirm/")
def confirm_staff_password_reset(new_password: str, confirm_new_password: str, token: str, db: Session = Depends(get_db)):
    if new_password != confirm_new_password:
        raise_http_exception(status.HTTP_400_BAD_REQUEST, "Passwords do not match")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # validate token
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        if user_type not in ('staff', 'superadmin'):
            raise_http_exception(status.HTTP_400_BAD_REQUEST, "Invalid Token")
    except JWTError:
        raise_http_exception(status.HTTP_400_BAD_REQUEST, "Invalid token")

    if user_type == "staff":
        db_staff = db.query(Staff).filter(Staff.id == user_id).first()
        if not db_staff:
            raise_http_exception(status.HTTP_404_NOT_FOUND, "Staff not found")
        hashed_password = get_password_hash(new_password)
        db_staff.password = hashed_password
        db.commit()
    elif user_type == "superadmin":
        db_superadmin = db.query(SuperAdmin).filter(SuperAdmin.id == user_id).first()
        if not db_superadmin:
            raise_http_exception(status.HTTP_404_NOT_FOUND, "SuperAdmin not found")
        hashed_password = get_password_hash(new_password)
        db_superadmin.password = hashed_password
        db.commit()

    return {"message": "Password reset successfully"}

# --- Staff Endpoints ---
#  Authorization:  Check user type and permissions
def is_staff_or_superadmin(current_user):
    if not isinstance(current_user, Staff) and not isinstance(current_user, SuperAdmin):
        raise_http_exception(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user

# 14. Staff Manage Orders and Customers
@app.get("/api/admin/orders/", response_model=List[OrderRead])
def get_orders(current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
    is_staff_or_superadmin(current_user)
    orders = db.query(Order).all()
    return orders

@app.get("/api/admin/orders/{order_id}/", response_model=OrderRead)
def get_order(order_id: int, current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
    is_staff_or_superadmin(current_user)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    return order

@app.patch("/api/admin/orders/{order_id}/assign-driver/", response_model=OrderRead)
def assign_driver_to_order(
    order_id: int,
    driver_id: int,
    current_user: Staff = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_staff_or_superadmin(current_user)
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    db_driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not db_driver:
        raise_http_exception(status.HTTP_400_BAD_REQUEST, "Driver not found")
    db_order.driver_id = driver_id
    db_order.staff_assigned_id = current_user.id
    db.commit()
    db.refresh(db_order)
    return db_order

@app.patch("/api/admin/orders/{order_id}/set-charge/", response_model=OrderRead)
def set_driver_charge(
    order_id: int,
    driver_charge: float,
    current_user: Staff = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_staff_or_superadmin(current_user)
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    if db_order.status != OrderStatus.PAIRING:
        raise_http_exception(
            status.HTTP_400_BAD_REQUEST, "Charge can only be set for orders in 'pairing' status"
        )
    db_order.driver_charge = driver_charge
    db.order.staff_assigned_id = current_user.id
    db.commit()
    db.refresh(db_order)
    return db_order

# Endpoint to accept driver charge and update order status
@app.post("/api/customers/orders/{order_id}/accept-charge/")
def accept_driver_charge(
    order_id: int,
    current_customer: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accept the driver's charge for an order and update the order status.
    """
    db_order = db.query(Order).filter(Order.id == order_id, Order.customer_id == current_customer.id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    if db_order.status != OrderStatus.PAIRING:
        raise HTTPException(
            status_code=400,
            detail=f"Order is not in 'pairing' status.  Current status is {db_order.status}",
        )

    if db_order.driver_charge is None:
        raise HTTPException(
            status_code=400, detail="Driver charge has not been set for this order."
        )
    #  Here you would integrate with your payment gateway
    #  For this example, we'll just simulate a successful payment
    #  You'll need to replace this with actual payment processing logic
    print(f"Simulating payment for order {order_id} for {db_order.driver_charge}")
    payment_successful = True  # Replace with your payment gateway's response

    if payment_successful:
        db_order.status = OrderStatus.PENDING_PAYMENT # set status to pending payment.
        db.commit()
        db.refresh(db_order)
        return {"message": "Payment successful.  Awaiting dispatch.", "order": db_order}
    else:
        raise HTTPException(status_code=400, detail="Payment failed")

@app.patch("/api/admin/orders/{order_id}/dispatch/", response_model=OrderRead)
def dispatch_order(order_id: int, current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
    is_staff_or_superadmin(current_user)
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    if db_order.status != OrderStatus.PENDING_PAYMENT: # changed from pairing to pending_payment
        raise_http_exception(
            status.HTTP_400_BAD_REQUEST, "Order must be in 'pending_payment' status to be dispatched"
        )
    db_order.status = OrderStatus.EN_ROUTE
    db.commit()
    db.refresh(db_order)
    return db_order

@app.patch("/api/admin/orders/{order_id}/delivered/", response_model=OrderRead)
def mark_order_as_delivered(
    order_id: int, current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)
):
    is_staff_or_superadmin(current_user)
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Order not found")
    if db_order.status != OrderStatus.EN_ROUTE:
        raise_http_exception(
            status.HTTP_400_BAD_REQUEST, "Order must be 'en-route' to be marked as delivered"
        )
    db_order.status = OrderStatus.DELIVERED
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/api/admin/customers/", response_model=List[CustomerRead])
def get_customers(current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
    is_staff_or_superadmin(current_user)
    customers = db.query(Customer).all()
    return customers

@app.get("/api/admin/customers/{customer_id}/", response_model=CustomerRead)
def get_customer(customer_id: int, current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
    is_staff_or_superadmin(current_user)
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Customer not found")
    return customer

# 15. Staff Create Driver
@app.post("/api/admin/drivers/", response_model=DriverRead, status_code=status.HTTP_201_CREATED)
def create_driver(driver: DriverCreate, current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
    is_staff_or_superadmin(current_user)
    db_driver = Driver(
        first_name=driver.first_name,
        last_name=driver.last_name,
        phone_number=driver.phone_number,
        vehicle_details=driver.vehicle_details,
        is_active=driver.is_active
    )
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver

# 16. Staff Preview Drivers
@app.get("/api/admin/drivers/", response_model=List[DriverRead])
def get_drivers(current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
    is_staff_or_superadmin(current_user)
    drivers = db.query(Driver).all()
    return drivers

@app.get("/api/admin/drivers/{driver_id}/", response_model=DriverRead)
def get_driver(driver_id: int, current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
    is_staff_or_superadmin(current_user)
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Driver not found")
    return driver

# --- Super Admin Endpoints ---
def is_superadmin(current_user):
    if not isinstance(current_user, SuperAdmin):
        raise_http_exception(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.  Must be a superadmin.",
        )
    return current_user

# 10. Super Admin Create Staff
@app.post("/api/superadmin/staff/", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
def create_staff(staff: StaffCreate, current_user: SuperAdmin = Depends(get_current_user), db: Session = Depends(get_db)):
    is_superadmin(current_user)
    db_staff = db.query(Staff).filter(Staff.email == staff.email).first()
    if db_staff:
        raise_http_exception(status.HTTP_400_BAD_REQUEST, "Email already registered")
    hashed_password = get_password_hash(staff.password)
    db_staff = Staff(
        first_name=staff.first_name,
        last_name=staff.last_name,
        email=staff.email,
        password=hashed_password,
        created_by_id=current_user.id,
    )
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff

# 11. Super Admin Manage Staff
@app.get("/api/superadmin/staff/", response_model=List[StaffRead])
def get_staff_members(current_user: SuperAdmin = Depends(get_current_user), db: Session = Depends(get_db)):
    is_superadmin(current_user)
    staff_members = db.query(Staff).all()
    return staff_members

@app.get("/api/superadmin/staff/{staff_id}/", response_model=StaffRead)
def get_staff_member(staff_id: int, current_user: SuperAdmin = Depends(get_current_user), db: Session = Depends(get_db)):
    is_superadmin(current_user)
    staff_member = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff_member:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Staff member not found")
    return staff_member

@app.patch("/api/superadmin/staff/{staff_id}/update/", response_model=StaffRead)
def update_staff_member(
    staff_id: int, staff: StaffCreate, current_user: SuperAdmin = Depends(get_current_user), db: Session = Depends(get_db)
):
    is_superadmin(current_user)
    db_staff_member = db.query(Staff).filter(Staff.id == staff_id).first()
    if not db_staff_member:
        raise_http_exception(status.HTTP_404_NOT_FOUND, "Staff member not found")
    db_staff_member.first_name = staff.first_name
    db_staff_member.last_name = staff.last_name
    db_staff_member.email = staff.email
    db_staff_member.password = get_password_hash(staff.password)
    db.staff_member.created_by_id = current_user.id
    db.commit()
    db.refresh(db_staff_member)
    return db_staff_member

# 8. Super Admin can be created -  Create Super Admin.  This should be done
#  via a script or initial setup, *not* via an API endpoint.
#  Example (do NOT include this in your main FastAPI app):
def create_super_admin():
    """
    Creates the initial superadmin user.  This should only be run once,
    during initial database setup.
    """
    db = SessionLocal()
    if db.query(SuperAdmin).first():
        print("SuperAdmin already exists.")
        db.close()
        return
    email = "superadmin@example.com"  #  Use a secure method to get this
    password = "superadminpassword"  #  MUST be replaced, and hashed
    hashed_password = get_password_hash(password)
    superadmin = SuperAdmin(email=email, password=hashed_password)
    db.add(superadmin)
    db.commit()
    print("SuperAdmin created.")
    db.close()

# 9. Super Admin password reset.  (See Staff password reset)  /api/admin/password/reset/request/
# 12. Staff can log into app (See Staff Login) /api/admin/login/
# 13. Staff can reset password (See Staff password reset)  /api/admin/password/reset/request/

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    #  Only run this *once* during initial setup:
    create_super_admin()
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
