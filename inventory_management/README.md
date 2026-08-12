# Inventory Management System (Django REST Framework)

A small DRF API for managing an inventory: custom user accounts, product
categories, products, customers, and sales invoices with a summary report.

## Stack

- Django 6.1
- Django REST Framework 3.18
- SQLite (default, zero-config)
- Token authentication (`rest_framework.authtoken`)

## Features

1. **Custom User model** (`accounts.User`) built on `AbstractUser`, with a
   custom manager (`CustomUserManager`) handling `create_user` /
   `create_superuser`, plus extra profile fields (`phone_number`,
   `address`, `date_of_birth`).
2. **Profile management** — a logged-in user can view/update their own
   profile (username/email are read-only there).
3. **Category, Customer & Product CRUD.**
4. **Invoice management** — an invoice ties a customer, a product, a
   quantity, and a unit price together; creating one automatically
   decrements product stock, and you can't invoice more than what's in
   stock.
5. **Serializers with field-level validation** (positive prices/quantities,
   stock checks, name/phone formatting, etc.) — see `validate_<field>`
   methods in each `serializers.py`.
6. **Permission classes** — reading is open to any authenticated user;
   only staff can create/update/delete categories, customers, and
   products; invoices can be created by any authenticated user but only
   edited/deleted by their creator or staff.
7. **Invoice report** — total invoices, total sales revenue, total product
   units sold.

## Project layout

```
inventory_management/
├── accounts/            # custom User model, profile & registration API
├── inventory/            # Category, Customer, Product, Invoice + report
├── inventory_management/ # project settings/urls
├── manage.py
└── requirements.txt
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The API is served from `http://127.0.0.1:8000/`.

## Authentication

Token auth is enabled. Register, then request a token:

```bash
curl -X POST http://127.0.0.1:8000/api/accounts/register/ \
  -d "username=alice&email=alice@example.com&password=S3curePass!23&password_confirm=S3curePass!23"

curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -d "username=alice&password=S3curePass!23"
# -> {"token": "..."}
```

Then send `Authorization: Token <token>` on subsequent requests. (Session
auth also works if you log into `/admin/` first, e.g. for browsing the
browsable API.)

## Endpoints

| Endpoint | Methods | Who |
|---|---|---|
| `/api/accounts/register/` | POST | anyone |
| `/api/auth/token/` | POST | anyone (returns auth token) |
| `/api/accounts/profile/` | GET, PUT, PATCH | authenticated (self only) |
| `/api/inventory/categories/` | GET, POST | GET: authenticated · POST/PUT/DELETE: staff |
| `/api/inventory/categories/{id}/` | GET, PUT, PATCH, DELETE | same as above |
| `/api/inventory/customers/` | GET, POST | GET: authenticated · write: staff |
| `/api/inventory/customers/{id}/` | GET, PUT, PATCH, DELETE | same as above |
| `/api/inventory/products/` | GET, POST | GET: authenticated · write: staff |
| `/api/inventory/products/{id}/` | GET, PUT, PATCH, DELETE | same as above |
| `/api/inventory/invoices/` | GET, POST | authenticated (creator recorded automatically) |
| `/api/inventory/invoices/{id}/` | GET, PUT, PATCH, DELETE | write: creator or staff |
| `/api/inventory/reports/summary/` | GET | authenticated |

### Example: create a product (staff token required)

```bash
curl -X POST http://127.0.0.1:8000/api/inventory/products/ \
  -H "Authorization: Token <staff-token>" \
  -d "name=Wireless Mouse&category=1&sku=SKU-001&price=19.99&stock_quantity=50"
```

### Example: create an invoice

```bash
curl -X POST http://127.0.0.1:8000/api/inventory/invoices/ \
  -H "Authorization: Token <token>" \
  -d "customer=1&product=1&quantity=2&unit_price=19.99"
```

### Example: report summary

```bash
curl http://127.0.0.1:8000/api/inventory/reports/summary/ \
  -H "Authorization: Token <token>"
# -> {"total_invoices": 3, "total_sales": "59.97", "total_products_sold": 3}
```

## Running tests

```bash
python manage.py test
```

9 tests cover registration/profile, product permission enforcement,
validation errors, invoice stock deduction, stock-limit rejection, and
ownership-based edit permissions on invoices.
