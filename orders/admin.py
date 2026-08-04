from django.contrib import admin
from .models import Invoice, Order, OrderItem, OrderStatusHistory, ReturnRequest


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "variant", "quantity", "unit_price_snapshot")


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("status", "note", "changed_at", "changed_by")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "user", "status", "grand_total", "placed_at")
    list_filter = ("status", "placed_at")
    search_fields = ("order_number", "user__username", "user__email")
    date_hierarchy = "placed_at"
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    readonly_fields = ("order_number", "placed_at", "updated_at")
    list_per_page = 25


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ("order_item", "reason", "status", "requested_at")
    list_filter = ("status", "reason")
    search_fields = ("order_item__order__order_number",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("order", "invoice_number", "generated_at")
    search_fields = ("invoice_number", "order__order_number")
