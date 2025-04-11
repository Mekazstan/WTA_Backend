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

### Customer Authentication:

* `POST /api/customers/register`: For new customer registration.
* `POST /api/customers/login`: For customer login and session management.
* `GET /api/customers/refresh_token`: To refresh the access token using a valid refresh token.
* `GET /api/customers/logout`: To revoke the current access token (logout).

### Customer Profile Management:

* `GET /api/customers/profile`: To retrieve customer profile details (requires authentication).
* `PUT /api/customers/profile`: To update customer profile details (requires authentication).
* `GET /api/customers/orders`: To retrieve the logged-in customer's order history (requires authentication).

### Order Management (Customer Side):

* `POST /api/orders`: To place a new order (requires customer authentication).

### Payment Integration:

* `POST /api/payments`: To initiate a payment (requires authentication, details depend on the payment gateway).
* `GET /api/payments/{payment_id}`: To retrieve payment details (requires authentication).
    * **Note:** Endpoints for verifying payment status (e.g., from a webhook) might be added depending on the payment gateway.

### Feedback and Ratings:

* `POST /api/feedback/{order_id}`: To submit feedback and a rating for a completed order (requires customer authentication).

### Driver Authentication:

* `POST /api/drivers/register`: For new driver registration.
* `POST /api/drivers/login`: For driver login and session management.
* `GET /api/drivers/refresh_token`: To refresh the driver's access token.
* `GET /api/drivers/logout`: To revoke the driver's access token (logout).

### Driver Profile Management:

* `GET /api/drivers/profile`: To retrieve driver profile details (requires driver authentication).
* `PUT /api/drivers/profile`: To update driver profile details (requires driver authentication).

### Admin Authentication:

* `POST /api/admin/signup`: For new admin user registration.
* `POST /api/admin/login`: For admin login and session management.
* `GET /api/admin/refresh_token`: To refresh the admin's access token.
* `GET /api/admin/logout`: To revoke the admin's access token (logout).

### Admin User Management:

* `GET /api/admin/customers`: To list all customers (requires admin authentication).
* `GET /api/admin/customers/{customer_id}`: To retrieve details of a specific customer (requires admin authentication).
* `POST /api/admin/customers`: To add a new customer (requires admin authentication).
* `PUT /api/admin/customers/{customer_id}`: To update customer details (requires admin authentication).
* `DELETE /api/admin/customers/{customer_id}`: To deactivate a customer account (requires admin authentication).

### Admin Driver Management:

* `GET /api/admin/drivers`: To list all drivers (requires admin authentication).
* `GET /api/admin/drivers/{driver_id}`: To retrieve details of a specific driver (requires admin authentication).
* `POST /api/admin/drivers`: To add a new driver (requires admin authentication).
* `PUT /api/admin/drivers/{driver_id}`: To update driver information (requires admin authentication).
* `DELETE /api/admin/drivers/{driver_id}`: To deactivate a driver (requires admin authentication).

### Admin Order Management:

* `GET /api/admin/orders`: To list all orders (requires admin authentication).
* `GET /api/admin/orders/{order_id}`: To retrieve details of a specific order (requires admin authentication).
* `PUT /api/admin/orders/{order_id}/assign`: To manually assign an order to a driver (requires admin authentication).
* `PUT /api/admin/orders/{order_id}/status`: To manually update the delivery status of an order (requires admin authentication).

### Admin Reporting:

* `GET /api/admin/reports/orders`: To generate reports on order statistics (requires admin authentication).
* `GET /api/admin/reports/revenue`: To generate revenue reports (requires admin authentication).
* `GET /api/admin/reports/feedback`: To retrieve feedback trends (requires admin authentication).


## Data Models

The backend utilizes the following data models (corresponding to database tables):

* `Customer`
* `Driver`
* `Order`
* `Payment`
* `Feedback`
* `AdminUser`

