from django.contrib import messages
from django.shortcuts import redirect
from django.views import View

from cart.models import Cart
from .models import Coupon


def _get_cart(request):
    buy_now = request.session.get("buy_now_session")
    if buy_now:
        from catalog.models import Product
        from orders.views import BuyNowCart
        product = Product.objects.filter(pk=buy_now["product_id"], is_published=True).first()
        if product and product.in_stock:
            quantity = buy_now.get("quantity", 1)
            return BuyNowCart(product, quantity)

    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).first()
    session_key = request.session.session_key
    if not session_key:
        return None
    return Cart.objects.filter(session_key=session_key).first()


class ApplyCouponView(View):
    def post(self, request):
        code = request.POST.get("code", "").strip().upper()
        redirect_url = request.META.get("HTTP_REFERER") or "cart:detail"

        if not code:
            messages.error(request, "Please enter a coupon code.")
            return redirect(redirect_url)

        coupon = Coupon.objects.filter(code__iexact=code).first()
        if not coupon:
            messages.error(request, f"Coupon code '{code}' does not exist.")
            return redirect(redirect_url)

        if not coupon.is_active:
            messages.error(request, f"Coupon code '{code}' is currently inactive.")
            return redirect(redirect_url)

        if not coupon.is_valid_now(request.user):
            messages.error(request, f"Coupon code '{code}' has expired or reached its usage limit.")
            return redirect(redirect_url)

        cart = _get_cart(request)
        cart_subtotal = cart.subtotal if cart else 0

        if coupon.min_order_value and cart_subtotal < coupon.min_order_value:
            messages.error(request, f"Minimum order value for coupon '{code}' is ₹{coupon.min_order_value}.")
            return redirect(redirect_url)

        request.session["coupon_code"] = coupon.code
        messages.success(request, f"Coupon '{coupon.code}' applied successfully!")
        return redirect(redirect_url)


class RemoveCouponView(View):
    def post(self, request):
        request.session.pop("coupon_code", None)
        messages.info(request, "Coupon removed.")
        return redirect(request.META.get("HTTP_REFERER", "cart:detail"))


from django.http import JsonResponse
from django.views.generic import ListView


class CouponListView(ListView):
    model = Coupon
    template_name = "coupons/list.html"
    context_object_name = "coupons"

    def get_queryset(self):
        return Coupon.objects.filter(is_active=True).order_by("-valid_from")


class CouponDetailApiView(View):
    def get(self, request, code):
        coupon = Coupon.objects.filter(code__iexact=code.strip(), is_active=True).first()
        if not coupon or not coupon.is_valid_now(request.user):
            return JsonResponse({"valid": False, "error": "Invalid or expired coupon code."}, status=404)
        data = coupon.to_dict()
        data["valid"] = True
        return JsonResponse(data)


