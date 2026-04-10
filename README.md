# The Laddoo House — Django Project

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the server
```bash
python manage.py runserver
```

That's it! Database is already set up with your 8 products.

## Login Credentials

**Admin Dashboard:** http://localhost:8000/dashboard/
- Username: `admin`
- Password: `laddoo123`

**Store (Customer Site):** http://localhost:8000/

## What's included
- `/` — Customer storefront with cart, checkout, UPI/Pay Later
- `/dashboard/` — Admin panel (orders, products CRUD)
- `/dashboard/products/` — Add / Edit / Hide / Delete products
- SQLite database with all 8 laddoos pre-loaded

## Before going live, update in `laddoohouse/settings.py`:
- `WHATSAPP_NUMBER` — your WhatsApp number
- `UPI_ID` — your UPI ID
- `OWNER_EMAIL` — your email
- `SECRET_KEY` — change to a secure random string
- `DEBUG = False`

## Project Structure
```
laddoohouse/
├── store/          # Customer-facing app (models, views, urls)
├── dashboard/      # Admin panel app
├── templates/      # All HTML templates
├── media/          # Uploaded payment screenshots
├── db.sqlite3      # SQLite database (already migrated + seeded)
└── manage.py
```
# laddoohouse
