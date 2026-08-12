from decimal import Decimal
import logging
import urllib.parse
import uuid

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

import re

from accounts.models import Address
from accounts.views import NeverCacheLoginRequiredMixin
from cart.models import Cart
from catalog.models import Product
from coupons.models import Coupon
from dashboard.models import StoreSettings
from payments.models import Payment
from .models import Order, OrderItem, ReturnRequest

logger = logging.getLogger("orders")


def _get_cart(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).first()
    return None



class BuyNowCartItem:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity
        self.unit_price = product.price
        self.line_total = product.price * quantity
        self.variant = None


class BuyNowCart:
    def __init__(self, product, quantity):
        item = BuyNowCartItem(product, quantity)
        self._item = item
        self.subtotal = item.line_total

    @property
    def items(self):
        class ItemsQuerySet:
            def __init__(self, item):
                self._items = [item]

            def all(self):
                return self._items

            def count(self):
                return 1

        return ItemsQuerySet(self._item)


class BuyNowView(View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id, is_published=True)

        if not product.in_stock:
            messages.error(request, f"Sorry, '{product.name}' is currently out of stock.")
            return redirect(product.get_absolute_url())

        try:
            quantity = int(request.POST.get("quantity", 1))
        except (ValueError, TypeError):
            quantity = 1

        if quantity < 1:
            quantity = 1

        if quantity > product.stock_quantity:
            messages.error(
                request,
                f"Sorry, only {product.stock_quantity} unit(s) of '{product.name}' available in stock.",
            )
            return redirect(product.get_absolute_url())

        # Store Buy Now temporary session context
        request.session["buy_now_session"] = {
            "product_id": str(product.id),
            "quantity": quantity,
        }

        checkout_url = reverse("orders:checkout")
        if not request.user.is_authenticated:
            login_url = reverse("accounts:login")
            messages.info(request, "Please log in to complete your checkout.")
            return redirect(f"{login_url}?next={checkout_url}")

        return redirect("orders:checkout")


class CheckoutView(NeverCacheLoginRequiredMixin, View):

    def _get_active_checkout_cart(self, request):
        buy_now = request.session.get("buy_now_session")
        if buy_now:
            product = Product.objects.filter(pk=buy_now["product_id"], is_published=True).first()
            if not product or not product.in_stock:
                request.session.pop("buy_now_session", None)
                messages.error(request, "The selected product is no longer available.")
                return None, True
            quantity = buy_now.get("quantity", 1)
            if quantity > product.stock_quantity:
                quantity = product.stock_quantity
            return BuyNowCart(product, quantity), True
        return _get_cart(request), False

    def get(self, request):
        cart, is_buy_now = self._get_active_checkout_cart(request)
        if not cart or cart.items.count() == 0:
            messages.warning(request, "Your cart is empty. Add items before checking out.")
            return redirect("cart:detail")

        subtotal = cart.subtotal
        coupon_code = request.session.get("coupon_code")
        coupon = None
        discount_total = Decimal("0.00")
        if coupon_code:
            coupon = Coupon.objects.filter(code__iexact=coupon_code, is_active=True).first()
            if coupon and coupon.is_valid_now(request.user):
                discount_total = Decimal(str(coupon.calculate_discount(subtotal)))
            else:
                coupon = None

        store_settings = StoreSettings.get_solo()
        discounted_subtotal = max(0, subtotal - discount_total)
        free_shipping_min = store_settings.free_shipping_threshold or Decimal("5000.00")
        std_shipping_fee = store_settings.standard_shipping_fee or Decimal("150.00")
        shipping_fee = Decimal("0.00") if discounted_subtotal >= free_shipping_min else std_shipping_fee
        grand_total = discounted_subtotal + shipping_fee

        if not store_settings.merchant_upi_id or not store_settings.whatsapp_notify_number:
            messages.error(
                request,
                "Order checkout is currently disabled because store payment settings (Merchant UPI ID or WhatsApp notify number) are not configured. Please contact the store administrator."
            )
            return redirect("cart:detail")

        txn_ref = request.session.get("checkout_txn_ref")
        if not txn_ref:
            txn_ref = f"TRX{uuid.uuid4().hex[:12].upper()}"
            request.session["checkout_txn_ref"] = txn_ref

        merchant_upi = store_settings.merchant_upi_id
        merchant_name = store_settings.merchant_name or "Store"
        merchant_name_enc = urllib.parse.quote(merchant_name)
        upi_link = f"upi://pay?pa={merchant_upi}&pn={merchant_name_enc}&am={grand_total:.2f}&cu=INR&tr={txn_ref}&tn=Order_Checkout"
        qr_preview_url = f"{reverse('payments:upi_qr_preview')}?am={grand_total:.2f}&tr={txn_ref}"

        total_mrp = Decimal("0.00")
        for item in cart.items.all():
            comp_price = item.product.compare_at_price
            item_mrp = comp_price if (comp_price and comp_price > item.unit_price) else item.unit_price
            total_mrp += (item_mrp * item.quantity)
        mrp_discount = max(Decimal("0.00"), total_mrp - subtotal)

        addresses = request.user.addresses.all()
        return render(request, "orders/checkout.html", {
            "cart": cart,
            "addresses": addresses,
            "is_buy_now": is_buy_now,
            "subtotal": subtotal,
            "total_mrp": total_mrp,
            "mrp_discount": mrp_discount,
            "coupon": coupon,
            "discount_total": discount_total,
            "shipping_fee": shipping_fee,
            "grand_total": grand_total,
            "transaction_ref": txn_ref,
            "upi_link": upi_link,
            "merchant_upi_id": merchant_upi,
            "merchant_name": merchant_name,
            "qr_preview_url": qr_preview_url,
        })

    def post(self, request):
        store_settings = StoreSettings.get_solo()
        if not store_settings.merchant_upi_id or not store_settings.whatsapp_notify_number:
            messages.error(
                request,
                "Order placement failed because store payment settings (Merchant UPI ID or WhatsApp notify number) are missing. Please contact the store administrator."
            )
            return redirect("cart:detail")

        cart, is_buy_now = self._get_active_checkout_cart(request)
        if not cart or cart.items.count() == 0:
            messages.error(request, "Your cart is empty.")
            return redirect("cart:detail")

        if not request.POST.get("payment_completed"):
            messages.error(request, "Please confirm that you have completed the payment via UPI QR code before placing your order.")
            return self.get(request)

        address_id = request.POST.get("address_id")
        address = None

        if address_id:
            address = Address.objects.filter(id=address_id, user=request.user).first()

        if not address:
            # Create new address from form POST data
            full_name = request.POST.get("full_name", "").strip()
            phone_number = request.POST.get("phone_number", "").strip()
            line1 = request.POST.get("line1", "").strip()
            line2 = request.POST.get("line2", "").strip()
            city = request.POST.get("city", "").strip()
            state = request.POST.get("state", "").strip()
            postal_code = request.POST.get("postal_code", "").strip()

            if not all([full_name, phone_number, line1, city, state, postal_code]):
                messages.error(request, "Please fill in all required address fields or select a saved address.")
                return self.get(request)

            address = Address.objects.create(
                user=request.user,
                full_name=full_name,
                phone_number=phone_number,
                line1=line1,
                line2=line2,
                city=city,
                state=state,
                postal_code=postal_code,
                country="India",
                is_default=(request.user.addresses.count() == 0),
            )

        try:
            with transaction.atomic():
                # Validate stock availability with select_for_update
                for item in cart.items.all():
                    product = Product.objects.select_for_update().get(pk=item.product.pk)
                    if item.quantity > product.stock_quantity:
                        messages.error(request, f"Sorry, '{product.name}' only has {product.stock_quantity} left in stock.")
                        return redirect("cart:detail")

                subtotal = cart.subtotal
                coupon_code = request.session.get("coupon_code")
                coupon = None
                discount_total = 0

                if coupon_code:
                    coupon = Coupon.objects.select_for_update().filter(code__iexact=coupon_code, is_active=True).first()
                    if coupon and coupon.is_valid_now(request.user):
                        discount_total = coupon.calculate_discount(subtotal)
                        coupon.times_used += 1
                        coupon.save(update_fields=["times_used"])
                    else:
                        coupon = None

                discounted_subtotal = max(0, subtotal - discount_total)
                shipping_fee = 0 if discounted_subtotal > 2000 else 150
                grand_total = discounted_subtotal + shipping_fee

                order = Order.objects.create(
                    user=request.user,
                    shipping_address=address,
                    status=Order.Status.PENDING,
                    subtotal=subtotal,
                    discount_total=discount_total,
                    shipping_fee=shipping_fee,
                    grand_total=grand_total,
                    coupon=coupon,
                )
                request.session.pop("coupon_code", None)

                # Create Payment record with unique transaction_ref and server-side validated amount
                transaction_ref = request.session.pop("checkout_txn_ref", None) or f"TRX{uuid.uuid4().hex[:12].upper()}"
                while Payment.objects.filter(transaction_ref=transaction_ref).exists():
                    transaction_ref = f"TRX{uuid.uuid4().hex[:12].upper()}"

                merchant_upi = store_settings.merchant_upi_id
                merchant_name = urllib.parse.quote(store_settings.merchant_name or "Store")
                upi_link = f"upi://pay?pa={merchant_upi}&pn={merchant_name}&am={grand_total:.2f}&cu=INR&tr={transaction_ref}&tn=Order_{order.order_number}"

                payment = Payment.objects.create(
                    order=order,
                    gateway=Payment.Gateway.UPI_QR,
                    transaction_ref=transaction_ref,
                    amount=grand_total,
                    status=Payment.Status.PENDING_VERIFICATION,
                    upi_link=upi_link,
                )

                items_summary_lines = []
                for idx, item in enumerate(cart.items.all(), start=1):
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        variant=item.variant,
                        product_name_snapshot=item.product.name,
                        unit_price_snapshot=item.unit_price,
                        quantity=item.quantity,
                    )
                    items_summary_lines.append(f"{idx}. *{item.product.name}* × {item.quantity} — ₹{item.line_total:,.2f}")

                    # Deduct stock with row locking
                    product = Product.objects.select_for_update().get(pk=item.product.pk)
                    product.stock_quantity = max(0, product.stock_quantity - item.quantity)
                    product.save(update_fields=["stock_quantity"])

                if is_buy_now:
                    request.session.pop("buy_now_session", None)
                else:
                    cart.items.all().delete()

            # Format complete WhatsApp order message
            items_text = "\n".join(items_summary_lines)
            addr = order.shipping_address
            address_str = f"{addr.line1}" + (f", {addr.line2}" if addr.line2 else "") + f", {addr.city}, {addr.state} - {addr.postal_code}"
            shipping_str = "FREE" if order.shipping_fee == 0 else f"₹{order.shipping_fee:,.2f}"

            discount_str = f"\n• *Discount:* -₹{order.discount_total:,.2f}" if order.discount_total > 0 else ""

            whatsapp_msg = (
                f"✨ *ETERNAAURA — NEW ORDER PLACED* ✨\n\n"
                f"📌 *ORDER DETAILS*\n"
                f"• *Order ID:* #{order.order_number}\n"
                f"• *Transaction Ref:* {payment.transaction_ref}\n"
                f"• *Date & Time:* {order.placed_at.strftime('%B %d, %Y at %I:%M %p')}\n"
                f"• *Payment Status:* Submitted via UPI QR (Pending Staff Verification)\n\n"
                f"👤 *CUSTOMER INFORMATION*\n"
                f"• *Name:* {addr.full_name}\n"
                f"• *Phone:* {addr.phone_number}\n"
                f"• *Shipping Address:* {address_str}\n\n"
                f"💎 *ORDERED PRODUCTS*\n"
                f"{items_text}\n\n"
                f"💰 *PAYMENT SUMMARY*\n"
                f"• *Subtotal:* ₹{order.subtotal:,.2f}"
                f"{discount_str}\n"
                f"• *Shipping Charge:* {shipping_str}\n"
                f"• *Total Amount:* ₹{order.grand_total:,.2f}\n\n"
                f"📝 *NOTES:* Customer completed UPI QR payment flow and submitted order. Pending staff verification."
            )

            target_phone = re.sub(r"\D", "", store_settings.whatsapp_notify_number)
            encoded_msg = urllib.parse.quote(whatsapp_msg)
            whatsapp_url = f"https://api.whatsapp.com/send?phone={target_phone}&text={encoded_msg}"

            messages.success(request, f"Order #{order.order_number} submitted! Payment status: Pending Verification.")
            return redirect(whatsapp_url)

        except Exception as e:
            logger.exception("Order placement failed for user %s", request.user.pk)
            messages.error(request, "Order placement failed due to an unexpected error. Please try again or contact support.")
            return self.get(request)



class OrderHistoryView(NeverCacheLoginRequiredMixin, ListView):
    template_name = "orders/history.html"
    context_object_name = "orders"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetailView(NeverCacheLoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class RequestReturnView(NeverCacheLoginRequiredMixin, View):
    def post(self, request, item_id):
        item = get_object_or_404(OrderItem, pk=item_id, order__user=request.user)
        ReturnRequest.objects.create(
            order_item=item,
            reason=request.POST.get("reason", ReturnRequest.Reason.OTHER),
            comment=request.POST.get("comment", ""),
        )
        return redirect("orders:detail", pk=item.order_id)

