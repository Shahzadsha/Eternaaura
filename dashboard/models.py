from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Records every meaningful admin action for the audit trail requirement."""
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="audit_logs")
    action = models.CharField(max_length=100)  # e.g. "product.update", "order.status_change"
    object_repr = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class LoginAttempt(models.Model):
    """Backs brute-force / login-attempt protection for the staff area."""
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    was_successful = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempted_at"]


class StoreSetting(models.Model):
    """Global store configuration managed by Super Admin."""
    store_name = models.CharField(max_length=150, default="ETERNAAURA")
    contact_email = models.EmailField(default="support@eternaaura.com")
    support_phone = models.CharField(max_length=30, default="+91 98765 43210")
    store_address = models.TextField(default="701, Eterna Towers, Bandra Kurla Complex, Mumbai, Maharashtra 400051")
    currency_symbol = models.CharField(max_length=10, default="₹")
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=3.00)
    standard_shipping_fee = models.DecimalField(max_digits=8, decimal_places=2, default=150.00)
    free_shipping_threshold = models.DecimalField(max_digits=8, decimal_places=2, default=5000.00)
    
    enable_razorpay = models.BooleanField(default=True)
    enable_stripe = models.BooleanField(default=True)
    enable_cod = models.BooleanField(default=True)
    enable_upi = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.store_name

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

