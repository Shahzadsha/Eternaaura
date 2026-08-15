from django.db import models
from .models import Cart


def clear_cart_cache(request):
    if hasattr(request, "_cached_cart"):
        delattr(request, "_cached_cart")


def _get_cart(request, force_refresh=False):
    if not force_refresh and hasattr(request, "_cached_cart"):
        return request._cached_cart
    user = getattr(request, "user", None)
    cart = None
    if user and user.is_authenticated:
        cart = Cart.objects.filter(user=user).annotate(total_qty=models.Sum("items__quantity")).first()
    else:
        session = getattr(request, "session", None)
        session_key = session.session_key if session else None
        if session_key:
            cart = Cart.objects.filter(session_key=session_key).annotate(total_qty=models.Sum("items__quantity")).first()
    request._cached_cart = cart
    return cart


def cart_summary(request):
    cart = _get_cart(request)
    if not cart:
        return {"cart_item_count": 0}
    count = getattr(cart, "total_qty", None)
    if count is None:
        count = cart.items.aggregate(total=models.Sum("quantity"))["total"] or 0
    return {
        "cart_item_count": count or 0,
    }
