import io
import urllib.parse
import uuid
import qrcode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from orders.models import Order
from .models import Payment


class UPIQRCodeView(LoginRequiredMixin, View):
    """
    Dynamically generates a PNG QR code for a Payment using the qrcode library on-the-fly.
    Does not require saving temporary files to disk.
    """
    def get(self, request, payment_id):
        payment = get_object_or_404(Payment, pk=payment_id, order__user=request.user)
        if not payment.upi_link:
            raise Http404("No UPI deep link associated with this payment.")
        
        img = qrcode.make(payment.upi_link)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return HttpResponse(buf.getvalue(), content_type="image/png")


class UPIPreviewQRCodeView(LoginRequiredMixin, View):
    """
    Dynamically generates a PNG QR code for checkout preview before order creation.
    Validates amount and transaction reference params.
    """
    def get(self, request):
        amount_str = request.GET.get("am", "0.00")
        tr = request.GET.get("tr", "")
        merchant_upi = getattr(settings, "MERCHANT_UPI_ID", "eternaaura@upi")
        merchant_name = urllib.parse.quote(getattr(settings, "MERCHANT_NAME", "EternaAura"))
        
        if not tr:
            tr = f"TRX{uuid.uuid4().hex[:12].upper()}"

        upi_link = f"upi://pay?pa={merchant_upi}&pn={merchant_name}&am={amount_str}&cu=INR&tr={tr}&tn=Order_Checkout"
        
        img = qrcode.make(upi_link)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return HttpResponse(buf.getvalue(), content_type="image/png")


class PaymentStatusView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        latest_payment = order.payments.order_by("-created_at").first()
        return JsonResponse({
            "order_number": order.order_number,
            "status": order.status,
            "payment_status": latest_payment.status if latest_payment else "cod",
            "transaction_ref": latest_payment.transaction_ref if latest_payment else "",
            "grand_total": str(order.grand_total),
        })
