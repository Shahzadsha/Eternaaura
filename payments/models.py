import uuid
from django.db import models


def generate_transaction_ref():
    return f"TRX{uuid.uuid4().hex[:12].upper()}"


class Payment(models.Model):
    class Gateway(models.TextChoices):
        RAZORPAY = "razorpay", "Razorpay"
        STRIPE = "stripe", "Stripe"
        UPI_QR = "upi_qr", "UPI QR Code"
        COD = "cod", "Cash on Delivery"

    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        PENDING_VERIFICATION = "pending_verification", "Pending Verification"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_ref = models.CharField(max_length=100, unique=True, db_index=True, null=True, blank=True)
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="payments")
    gateway = models.CharField(max_length=20, choices=Gateway.choices)
    gateway_payment_id = models.CharField(max_length=100, blank=True)
    gateway_order_id = models.CharField(max_length=100, blank=True)
    gateway_signature = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    upi_link = models.TextField(blank=True)
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.transaction_ref:
            self.transaction_ref = f"TRX{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment({self.transaction_ref}, {self.order.order_number}, {self.status})"

