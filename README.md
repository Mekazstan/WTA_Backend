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

### Customer API Endpoints

* `POST /api/customers/register`: Register a new customer.
* `POST /api/customers/login`: Log in an existing customer.
* `GET /api/customers/profile`: Get the logged-in customer's profile (requires authentication).
* `PUT /api/customers/profile`: Update the logged-in customer's profile (requires authentication).
* `POST /api/orders`: Place a new water tanker order (requires authentication).
* `GET /api/customers/orders`: Get the order history for the logged-in customer (requires authentication).
* `POST /api/orders/{order_id}/feedback`: Submit feedback and rating for a completed order (requires authentication).

### Admin API Endpoints

* `POST /api/admin/login`: Log in as an administrator.
* `GET /api/admin/customers`: Get a list of all customers (requires authentication).
* `GET /api/admin/customers/{customer_id}`: Get details of a specific customer (requires authentication).
* `PUT /api/admin/customers/{customer_id}`: Update customer details (requires authentication).
* `GET /api/admin/drivers`: Get a list of all drivers (requires authentication).
* `GET /api/admin/drivers/{driver_id}`: Get details of a specific driver (requires authentication).
* `POST /api/admin/drivers`: Add a new driver (requires authentication).
* `PUT /api/admin/drivers/{driver_id}`: Update driver information (requires authentication).
* `GET /api/admin/orders`: Get a list of all orders (requires authentication).
* `GET /api/admin/orders/{order_id}`: Get details of a specific order (requires authentication).
* `PUT /api/admin/orders/{order_id}/assign`: Manually assign an order to a driver (requires authentication).
* `PUT /api/admin/orders/{order_id}/status`: Manually update the delivery status of an order (requires authentication).
* `GET /api/admin/reports/orders`: Generate reports on order statistics (requires authentication).
* `GET /api/admin/reports/revenue`: Generate revenue reports (requires authentication).
* `GET /api/admin/reports/feedback`: Get feedback trends (requires authentication).


## Data Models

The backend utilizes the following data models (corresponding to database tables):

* `Customer`
* `Driver`
* `Order`
* `Payment`
* `Feedback`
* `AdminUser`

