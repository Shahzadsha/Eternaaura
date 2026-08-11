from django.contrib import admin
from .models import AuditLog, LoginAttempt, StoreSettings

admin.site.register(AuditLog)
admin.site.register(LoginAttempt)


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ("store_name", "merchant_upi_id", "merchant_name", "whatsapp_notify_number", "updated_at")
    fieldsets = (
        ("Merchant UPI & WhatsApp Settings", {
            "fields": ("merchant_upi_id", "merchant_name", "whatsapp_notify_number"),
            "description": "Merchant credentials used for dynamic UPI QR code generation and WhatsApp order notifications.",
        }),
        ("Store Information", {
            "fields": ("store_name", "contact_email", "support_phone", "store_address", "currency_symbol"),
        }),
        ("Delivery & Taxes", {
            "fields": ("tax_percentage", "standard_shipping_fee", "free_shipping_threshold"),
        }),
        ("Payment Gateways Enabled", {
            "fields": ("enable_upi", "enable_cod", "enable_razorpay", "enable_stripe"),
        }),
    )

    def has_module_permission(self, request):
        return bool(request.user and request.user.is_active and request.user.is_superuser)

    def has_view_permission(self, request, obj=None):
        return bool(request.user and request.user.is_active and request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        return bool(request.user and request.user.is_active and request.user.is_superuser)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

