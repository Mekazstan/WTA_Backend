# Water Tanker Availability Application - Backend

## Overview

This repository contains the backend implementation for the Water Tanker Availability application, as outlined in the Software Requirements Specification (SRS) document. This MVP backend provides the necessary APIs and data management for customers to place orders and for administrators to manage users, drivers, and deliveries manually.

## Technology Stack

* **Backend Framework:** FastAPI
* **Programming Language:** Python
* **Database:** PostgreSQL DB
* **ORM/ODM:** SQLAlchemy
* **API Documentation:** Swagger/OpenAPI
* **Authentication:** JWT (JSON Web Tokens)
* **Payment Gateway Integration:** Paystack / Flutterwave
* **Testing:** Pytest

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Mekazstan/WTA_Backend
    cd WTA_Backend
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the database:**
    * Create a database instance on PostgreSQL.
    * Update the database connection settings in your application's configuration file at `.env`.

4.  **Run database migrations:**
    ```bash
    (using Alembic)
    alembic db upgrade
    ```

5.  **Set up environment variables:**
    * Create a `.env` file (or equivalent) and configure sensitive information such as:
        * Database credentials
        * Secret keys for JWT
        * API keys for the payment gateway
        * Other environment-specific settings

6.  **Run the backend server:**
    ```bash
    fastapi dev main.py
    ```

## API Endpoints

This section details all the available API endpoints.

**Customers**

* **`POST /api/customers/register/`**: Registers a new customer.
* **`POST /api/customers/login/`**: Logs in an existing customer and returns an access token.
* **`POST /api/customers/password/reset/request/`**: Requests a password reset link to be sent to the customer's email.
* **`POST /api/customers/password/reset/confirm/`**: Confirms a password reset using a token received via email.
* **`POST /api/customers/orders/`**: Creates a new order for the authenticated customer.
* **`GET /api/customers/orders/`**: Retrieves a list of orders for the authenticated customer.
* **`GET /api/customers/orders/{order_id}/`**: Retrieves details of a specific order for the authenticated customer.
* **`PATCH /api/customers/orders/{order_id}/cancel/`**: Cancels a specific order for the authenticated customer, if it's in the appropriate status.
* **`POST /api/customers/recyclables/`**: Creates a new recyclable submission for the authenticated customer.
* **`GET /api/customers/recyclables/`**: Retrieves a list of recyclable submissions for the authenticated customer.
* **`GET /api/customers/recyclables/{submission_id}/`**: Retrieves details of a specific recyclable submission for the authenticated customer.
* **`POST /api/customers/orders/{order_id}/accept-charge/`**: Accepts the driver's charge for a specific order and proceeds with payment.

**Super Admin**

* **`POST /api/superadmin/staff/`**: Creates a new staff member (requires superadmin authentication).
* **`GET /api/superadmin/staff/`**: Retrieves a list of all staff members (requires superadmin authentication).
* **`GET /api/superadmin/staff/{staff_id}/`**: Retrieves details of a specific staff member (requires superadmin authentication).
* **`PATCH /api/superadmin/staff/{staff_id}/update/`**: Updates details of a specific staff member (requires superadmin authentication).

**Staff & Super Admin**

* **`POST /api/staff/login/`**: Logs in a staff member or a superadmin and returns an access token, along with the user type.
* **`POST /api/admin/password/reset/request/`**: Requests a password reset link for a staff member or superadmin.
* **`POST /api/admin/password/reset/confirm/`**: Confirms a password reset for a staff member or superadmin using a token.
* **`GET /api/admin/orders/`**: Retrieves a list of all orders (requires staff or superadmin authentication).
* **`GET /api/admin/orders/{order_id}/`**: Retrieves details of a specific order (requires staff or superadmin authentication).
* **`PATCH /api/admin/orders/{order_id}/assign-driver/`**: Assigns a driver to a specific order (requires staff or superadmin authentication).
* **`PATCH /api/admin/orders/{order_id}/set-charge/`**: Sets the driver's charge for a specific order (requires staff or superadmin authentication).
* **`PATCH /api/admin/orders/{order_id}/dispatch/`**: Marks a specific order as dispatched (requires staff or superadmin authentication).
* **`PATCH /api/admin/orders/{order_id}/delivered/`**: Marks a specific order as delivered (requires staff or superadmin authentication).
* **`GET /api/admin/customers/`**: Retrieves a list of all customers (requires staff or superadmin authentication).
* **`GET /api/admin/customers/{customer_id}/`**: Retrieves details of a specific customer (requires staff or superadmin authentication).
* **`POST /api/admin/drivers/`**: Creates a new driver (requires staff or superadmin authentication).
* **`GET /api/admin/drivers/`**: Retrieves a list of all drivers (requires staff or superadmin authentication).
* **`GET /api/admin/drivers/{driver_id}/`**: Retrieves details of a specific driver (requires staff or superadmin authentication).


## Data Models

The backend utilizes the following data models (corresponding to database tables):

* `Customer`
* `Order`
* `Driver`
* `Staff`
* `SuperAdmin`
* `RecyclableSubmission`

