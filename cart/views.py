from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from catalog.models import Product
from dashboard.models import StoreSettings
from .models import Cart, CartItem


def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key, user=None)
    return cart


def _safe_quantity(raw, default=1, minimum=1, maximum=None):
    try:
        qty = int(raw)
    except (TypeError, ValueError):
        return default
    qty = max(qty, minimum)
    if maximum is not None:
        qty = min(qty, maximum)
    return qty


from coupons.models import Coupon


class CartDetailView(View):
    def get(self, request):
        cart = _get_or_create_cart(request)
        coupon_code = request.session.get("coupon_code")
        coupon = None
        discount_amount = 0

        if coupon_code:
            coupon = Coupon.objects.filter(code__iexact=coupon_code, is_active=True).first()
            if coupon and coupon.is_valid_now():
                discount_amount = coupon.calculate_discount(cart.subtotal)
            else:
                request.session.pop("coupon_code", None)
                coupon = None

        store_settings = StoreSettings.get_solo()
        discounted_subtotal = max(0, cart.subtotal - discount_amount)
        free_shipping_min = store_settings.free_shipping_threshold or Decimal("5000.00")
        std_shipping_fee = store_settings.standard_shipping_fee or Decimal("150.00")
        shipping_fee = Decimal("0.00") if discounted_subtotal >= free_shipping_min else std_shipping_fee
        grand_total = discounted_subtotal + shipping_fee

        return render(request, "cart/detail.html", {
            "cart": cart,
            "coupon": coupon,
            "discount_amount": discount_amount,
            "shipping_fee": shipping_fee,
            "grand_total": grand_total,
        })


class AddToCartView(View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id, is_published=True)
        cart = _get_or_create_cart(request)
        quantity = _safe_quantity(request.POST.get("quantity"), default=1, maximum=max(product.stock_quantity, 0))
        item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=None)
        new_quantity = quantity if created else item.quantity + quantity
        item.quantity = min(new_quantity, product.stock_quantity) if product.stock_quantity else new_quantity
        item.save()
        return redirect("cart:detail")


class UpdateCartItemView(View):
    def post(self, request, item_id):
        cart = _get_or_create_cart(request)
        # Scoped to the requester's own cart — prevents editing another
        # customer's cart items by guessing item_id.
        item = get_object_or_404(CartItem, pk=item_id, cart=cart)
        quantity = _safe_quantity(
            request.POST.get("quantity"), default=item.quantity,
            minimum=0, maximum=item.product.stock_quantity or None,
        )
        if quantity > 0:
            item.quantity = quantity
            item.save()
        else:
            item.delete()
        return redirect("cart:detail")


class RemoveCartItemView(View):
    def post(self, request, item_id):
        cart = _get_or_create_cart(request)
        item = get_object_or_404(CartItem, pk=item_id, cart=cart)
        item.delete()
        return redirect("cart:detail")
