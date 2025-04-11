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

The backend exposes the following API endpoints:

###  Customer Authentication:

* `POST /api/customers/register`: For new customer registration.
* `POST /api/customers/login`: For customer login and session management (e.g., using JWT).

### Customer Profile Management:

* `GET /api/customers/profile`: To retrieve customer profile details.
* `PUT /api/customers/profile`: To update customer profile details.

### Order Management (Customer Side):

* `POST /api/orders`: To place a new order.
* `GET /api/customers/orders`: To retrieve a customer's order history.

### Payment Integration:

Endpoints to initiate and verify payments with the chosen payment gateway. This will likely involve interacting with a third-party API.

### Feedback and Ratings:

* `POST /api/orders/{order_id}/feedback`: To submit feedback and a rating for a completed order.

###  Admin Authentication:

* `POST /api/admin/login`: For admin login and session management.

### Admin User Management:

* `GET /api/admin/customers`: To list all customers (with optional filtering/pagination).
* `GET /api/admin/customers/{customer_id}`: To retrieve details of a specific customer.
* `POST /api/admin/customers`: To add a new customer (if needed).
* `PUT /api/admin/customers/{customer_id}`: To update customer details.
* `DELETE /api/admin/customers/{customer_id}`: To deactivate a customer account.

### Admin Driver Management:

* `GET /api/admin/drivers`: To list all drivers (with optional filtering).
* `GET /api/admin/drivers/{driver_id}`: To retrieve details of a specific driver.
* `POST /api/admin/drivers`: To add a new driver.
* `PUT /api/admin/drivers/{driver_id}`: To update driver information.
* `DELETE /api/admin/drivers/{driver_id}`: To deactivate a driver.

### Admin Order Management:

* `GET /api/admin/orders`: To list all orders (with filtering options based on status, date, etc.).
* `GET /api/admin/orders/{order_id}`: To retrieve details of a specific order.
* `PUT /api/admin/orders/{order_id}/assign`: To manually assign an order to a driver (requires driver_id in the request).
* `PUT /api/admin/orders/{order_id}/status`: To manually update the delivery status of an order.

### Admin Reporting:

* `GET /api/admin/reports/orders`: To generate reports on order statistics (e.g., total orders, completed orders).
* `GET /api/admin/reports/revenue`: To generate revenue reports (based on completed payments).
* `GET /api/admin/reports/feedback`: To retrieve feedback trends.


## Data Models

The backend utilizes the following data models (corresponding to database tables):

* `Customer`
* `Driver`
* `Order`
* `Payment`
* `Feedback`
* `AdminUser`

