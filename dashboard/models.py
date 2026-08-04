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
