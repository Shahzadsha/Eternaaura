from django.db import models
from .models import Cart


def _get_cart(request):
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        return Cart.objects.filter(user=user).first()
    session = getattr(request, "session", None)
    session_key = session.session_key if session else None
    if not session_key:
        return None
    return Cart.objects.filter(session_key=session_key).first()


def cart_summary(request):
    cart = _get_cart(request)
    if not cart:
        return {"cart_item_count": 0}
    count = cart.items.aggregate(total=models.Sum("quantity"))["total"] or 0
    return {
        "cart_item_count": count,
    }
