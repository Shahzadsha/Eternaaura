# ETERNAAURA — Luxury Jewellery E-Commerce (Django)

A premium jewellery storefront + private staff dashboard, built as modular Django apps
with Tailwind CSS, PostgreSQL (SQLite fallback for local dev), and a black/cream/gold
design system.

## What's in this build (Phase 1–2 foundation)

**Verified working right now:**
- Full project scaffold: `config` + apps `accounts`, `catalog`, `cart`, `orders`,
  `reviews`, `coupons`, `payments`, `dashboard`
- Custom `User` model (phone, email/OTP verification flags, staff role)
- Catalog models: Category, Collection, Product, ProductImage, ProductVariant,
  Product360View, ProductVideo, HeroBanner, Wishlist, RecentlyViewed
- Order/Cart/Coupon/Review/Payment models
- Storefront pages
- Staff dashboard
- RBAC
- Django Admin
- Demo data seeding

## Quick Start

```bash
python -m venv venv
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```