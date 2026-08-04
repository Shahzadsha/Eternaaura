from django.contrib import admin
from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "discount_value", "is_active", "valid_from", "valid_until", "times_used", "usage_limit")
    list_filter = ("is_active", "discount_type")
    search_fields = ("code", "description")
    list_editable = ("is_active",)
