import uuid
from django.db import models


class Payment(models.Model):
    class Gateway(models.TextChoices):
        RAZORPAY = "razorpay", "Razorpay"
        STRIPE = "stripe", "Stripe"
        COD = "cod", "Cash on Delivery"

    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="payments")
    gateway = models.CharField(max_length=20, choices=Gateway.choices)
    gateway_payment_id = models.CharField(max_length=100, blank=True)
    gateway_order_id = models.CharField(max_length=100, blank=True)
    gateway_signature = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment({self.order.order_number}, {self.status})"
