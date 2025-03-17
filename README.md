# Coderr

## Description
Coderr is a Django REST Framework (DRF) application for freelance IT services. Users can create accounts, post offers for services, place orders for available services, and submit reviews.

Please do also check out the ASP.NET Core version for this API under: https://github.com/mariuskas1/CoderrAPI/


---

## Tech Stack
- **Python**: 3.x
- **Django**: 5.1.5
- **Django REST Framework**: 3.15.2
- **Django Filter**: 24.3
- **CORS Headers**: 4.6.0
- **SQLParse**: 0.5.3
- **ASGIRef**: 3.8.1
- **Database**: SQLite 

---

## Installation

### Clone the Repository
```sh
git clone https://github.com/mariuskas1/coderr_backend.git
cd coderr_backend
```
### Create a Virtual Environment
```sh
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate  # Windows
```
### Install Dependencies
```sh
pip install -r requirements.txt
```
### Apply Migrations
```sh
python manage.py migrate
```
### Start the Development Server
```sh
python manage.py runserver
```
The API will be available at http://127.0.0.1:8000/

## API Endpoints

### Offers
* GET /offers/ - Retrieve a list of offers with filtering and search options
* POST /offers/ - Create a new offer with details
* GET /offers/{id}/ - Retrieve details of a specific offer
* PATCH /offers/{id}/ - Update a specific offer
* DELETE /offers/{id}/ - Delete a specific offer
* GET /offerdetails/{id}/ - Retrieve details of a specific offer detail

### Orders
* GET /orders/ - Retrieve the orders for the logged-in user
* POST /orders/ - Create a new order based on an offer
* GET /orders/{id}/ - Retrieve details of a specific order
* PATCH /orders/{id}/ - Update the status of a specific order
* DELETE /orders/{id}/ - Delete an order (Admin only)
* GET /order-count/{business_user_id}/ - Retrieve the count of active orders for a business user
* GET /completed-order-count/{business_user_id}/ - Retrieve the count of completed orders for a business user

### General Information
* GET /base-info/ - Retrieve general platform information

### User Profiles
* GET /profile/{id}/ - Retrieve details of a specific user
* PATCH /profile/{id}/ - Update details of a specific user
* GET /profiles/business/ - Retrieve a list of business user
* GET /profiles/customer/ - Retrieve a list of customer profiles

### Authentication & Registration
* POST /login/ - User login
* POST /registration/ - User registration

### Reviews 
* GET /reviews/ - Retrieve a list of reviews
* POST /reviews/ - Create a new review
* GET /reviews/{id}/ - Retrieve details of a specific review
* PATCH /reviews/{id}/ - Update a specific review
* DELETE /reviews/{id}/ - Delete a specific review






