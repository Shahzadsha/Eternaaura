from .models import Cart


def _get_cart(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).first()
    session_key = request.session.session_key
    if not session_key:
        return None
    return Cart.objects.filter(session_key=session_key).first()


def cart_summary(request):
    cart = _get_cart(request)
    return {
        "cart_item_count": cart.item_count if cart else 0,
    }
