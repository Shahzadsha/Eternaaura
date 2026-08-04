import uuid
from django.conf import settings
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Payment"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for Delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        RETURN_REQUESTED = "return_requested", "Return Requested"
        RETURNED = "returned", "Returned"
        REFUNDED = "refunded", "Refunded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")

    shipping_address = models.ForeignKey("accounts.Address", on_delete=models.PROTECT, related_name="+")
    billing_address = models.ForeignKey("accounts.Address", on_delete=models.PROTECT, related_name="+", null=True, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)

    coupon = models.ForeignKey("coupons.Coupon", on_delete=models.SET_NULL, null=True, blank=True)

    estimated_delivery_date = models.DateField(null=True, blank=True)
    tracking_number = models.CharField(max_length=60, blank=True)
    carrier = models.CharField(max_length=60, blank=True)

    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"EA{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True)
    product_name_snapshot = models.CharField(max_length=200)
    unit_price_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def line_total(self):
        return self.unit_price_snapshot * self.quantity


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=20, choices=Order.Status.choices)
    note = models.CharField(max_length=255, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-changed_at"]
        verbose_name_plural = "Order status histories"


class ReturnRequest(models.Model):
    class Reason(models.TextChoices):
        DAMAGED = "damaged", "Damaged product"
        WRONG_ITEM = "wrong_item", "Wrong item received"
        NOT_AS_DESCRIBED = "not_as_described", "Not as described"
        SIZE_ISSUE = "size_issue", "Size issue"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        PICKED_UP = "picked_up", "Picked up"
        REFUNDED = "refunded", "Refunded"

    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="return_requests")
    reason = models.CharField(max_length=20, choices=Reason.choices)
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    requested_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="invoice")
    invoice_number = models.CharField(max_length=30, unique=True)
    pdf_file = models.FileField(upload_to="invoices/", blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
