from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from orders.models import Order
from .models import Payment


class PaymentStatusView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        latest_payment = order.payments.first()
        return JsonResponse({
            "order_number": order.order_number,
            "status": order.status,
            "payment_status": latest_payment.status if latest_payment else "cod",
            "grand_total": str(order.grand_total),
        })
