from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    Category, Collection, HeroBanner, Product, ProductImage, Product360View,
    ProductVideo, ProductVariant, VariantAttribute, VariantValue, Wishlist, RecentlyViewed,
)

admin.site.site_header = "ETERNAAURA Admin"
admin.site.site_title = "ETERNAAURA Admin"
admin.site.index_title = "Store Management"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "thumbnail", "alt_text", "display_order")
    readonly_fields = ("thumbnail",)

    @admin.display(description="")
    def thumbnail(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" class="admin-thumb">', obj.image.url)
        return "—"


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("thumbnail", "name", "sku", "category", "price", "compare_at_price", "stock_quantity", "is_published", "is_featured")
    list_display_links = ("thumbnail", "name")
    list_filter = ("category", "is_published", "is_featured", "is_new_arrival", "is_best_seller", "is_trending")
    search_fields = ("name", "sku")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductVariantInline]
    filter_horizontal = ("collections", "manually_related_products")
    autocomplete_fields = ("category",)
    list_per_page = 25
    actions = ["publish_products", "unpublish_products", "duplicate_products"]

    @admin.display(description="Photo")
    def thumbnail(self, obj):
        first_image = obj.images.first() if obj.pk else None
        if first_image and first_image.image:
            return format_html('<img src="{}" class="admin-thumb">', first_image.image.url)
        return mark_safe('<div class="admin-thumb" style="background:#1b1b1e;"></div>')

    @admin.action(description="Publish selected products")
    def publish_products(self, request, queryset):
        queryset.update(is_published=True)

    @admin.action(description="Unpublish selected products")
    def unpublish_products(self, request, queryset):
        queryset.update(is_published=False)

    @admin.action(description="Duplicate selected products")
    def duplicate_products(self, request, queryset):
        for product in queryset:
            product.pk = None
            product.sku = f"{product.sku}-COPY"
            product.slug = ""
            product.name = f"{product.name} (Copy)"
            product.save()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("thumbnail", "name", "parent", "is_active", "display_order")
    list_display_links = ("thumbnail", "name")
    list_editable = ("display_order",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Photo")
    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" class="admin-thumb">', obj.image.url)
        return mark_safe('<div class="admin-thumb" style="background:#1b1b1e;"></div>')


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ("thumbnail", "title", "display_order", "is_active")
    list_display_links = ("thumbnail", "title")
    list_editable = ("display_order", "is_active")

    @admin.display(description="Photo")
    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" class="admin-thumb">', obj.image.url)
        return mark_safe('<div class="admin-thumb" style="background:#1b1b1e;"></div>')


admin.site.register(Product360View)
admin.site.register(ProductVideo)
admin.site.register(VariantAttribute)
admin.site.register(VariantValue)
admin.site.register(Wishlist)
admin.site.register(RecentlyViewed)
