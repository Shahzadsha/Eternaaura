from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Address, OTPVerification, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "is_superuser", "is_email_verified")
    list_filter = UserAdmin.list_filter + ("is_email_verified",)
    fieldsets = UserAdmin.fieldsets + (
        ("ETERNAAURA", {"fields": ("phone_number", "two_factor_enabled", "is_email_verified", "is_phone_verified")}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "city", "state", "address_type", "is_default")
    list_filter = ("address_type", "is_default", "state")
    search_fields = ("full_name", "user__username", "city", "postal_code")


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "purpose", "is_used", "created_at", "expires_at")
    list_filter = ("purpose", "is_used")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("code", "created_at")
