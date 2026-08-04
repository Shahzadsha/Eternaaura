"""
ETERNAAURA — Root URL configuration.

Note: the staff/admin area is mounted at settings.STAFF_LOGIN_PATH (default
"staff") and is NEVER linked from any customer-facing template.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Django's built-in admin is kept at a non-obvious path too, for superusers only.
    path("django-admin/", admin.site.urls),

    # Private staff dashboard (Phase 5) — e.g. /staff/login/, /staff/
    path(f"{settings.STAFF_LOGIN_PATH}/", include("dashboard.urls", namespace="dashboard")),

    path("account/", include("accounts.urls", namespace="accounts")),
    path("cart/", include("cart.urls", namespace="cart")),
    path("coupons/", include("coupons.urls", namespace="coupons")),
    path("orders/", include("orders.urls", namespace="orders")),
    path("payments/", include("payments.urls", namespace="payments")),
    path("reviews/", include("reviews.urls", namespace="reviews")),
    path("", include("catalog.urls", namespace="catalog")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
