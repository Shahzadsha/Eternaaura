# ETERNAAURA — Luxury Jewellery E-Commerce (Django)

A premium jewellery storefront + private staff dashboard, built as modular Django apps
with Tailwind CSS, PostgreSQL (SQLite fallback for local dev), and a black/cream/gold
design system.

## What's in this build (Phase 1–2 foundation)

**Verified working right now:**
- Full project scaffold: `config` + apps `accounts`, `catalog`, `cart`, `orders`,
  `reviews`, `coupons`, `payments`, `dashboard`
- Custom `User` model (phone, email/OTP verification flags, staff role)
- Catalog models: Category, Collection, Product (pricing, discount, stock, SEO,
  metal purity, gemstone, SKU), ProductImage, ProductVariant, Product360View,
  ProductVideo, HeroBanner, Wishlist, RecentlyViewed
- Order/Cart/Coupon/Review/Payment models
- Storefront pages rendering end-to-end: homepage (hero, categories, new arrivals,
  best sellers, trending, bridal/daily-wear collections), category pages, collection
  pages, search, product detail page, cart
- Auth pages: register, login (templates render; wire up email/OTP backend + Razorpay/
  Stripe keys before going live — see `.env.example`)
- **Private staff dashboard** at `/staff/login/` (path configurable via `STAFF_LOGIN_PATH`)
  — never linked from any customer-facing template. Dark theme with gold accents,
  gated by `is_staff`.
- **RBAC**: `User.staff_role` (Super Admin / Product Manager / Order Manager /
  Customer Support / Content Manager / Marketing Manager) auto-syncs to Django
  Groups + scoped permissions via a signal — see `dashboard/management/commands/
  setup_staff_roles.py`
- Full Django admin at `/django-admin/` for detailed catalog/order/coupon/review
  management (the custom `/staff/` dashboard is the polished overview + KPI layer
  on top of it)
- `seed_demo_data` management command populates realistic sample products so you
  can see the site immediately

**Not yet built (flagged honestly, not faked):**
- Razorpay/Stripe checkout flow wiring (models + settings are ready, views aren't)
- Email/SMS OTP delivery (console backend works for dev; needs a real provider)
- Invoice PDF generation, return/cancellation request views
- Product reviews with photo upload + Q&A UI
- Analytics charts (Chart.js) on the dashboard — page exists, data isn't wired yet
- 2FA enforcement, login-attempt throttling, audit log UI
- Image assets — seeded products have no real photos; upload via `/django-admin/`
  or extend `seed_demo_data` with real files

## Quick start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit as needed; leave POSTGRES_* blank to use SQLite

python manage.py migrate
python manage.py createsuperuser
python manage.py setup_staff_roles     # creates RBAC groups + permissions
python manage.py seed_demo_data        # sample categories/products for preview

python manage.py runserver
```

Visit:
- `http://127.0.0.1:8000/` — storefront
- `http://127.0.0.1:8000/staff/login/` — private staff dashboard (needs `is_staff=True`)
- `http://127.0.0.1:8000/django-admin/` — full Django admin

To give a staff user a role after creating them:
```python
from accounts.models import User
u = User.objects.get(username="someone")
u.is_staff = True
u.staff_role = User.StaffRole.PRODUCT_MANAGER
u.save()  # signal auto-adds them to the "Product Manager" group
```

## Switching to PostgreSQL

Set `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`,
`POSTGRES_PORT` in `.env` — `config/settings.py` picks it up automatically and
drops the SQLite fallback.

## Next steps

This is a foundation built to be extended, not a finished storefront. The
recommended next phase is checkout + payments (Razorpay test mode), since that's
the highest-value gap, followed by the dashboard analytics charts and review/Q&A UI.
