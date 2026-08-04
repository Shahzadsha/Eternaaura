from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("product", "variant", "quantity", "added_at")
    can_delete = True


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("__str__", "user", "session_key", "item_count", "subtotal", "updated_at")
    search_fields = ("user__username", "user__email", "session_key")
    inlines = [CartItemInline]
    readonly_fields = ("created_at", "updated_at")
