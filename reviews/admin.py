from django.contrib import admin
from django.utils.html import format_html
from .models import ProductAnswer, ProductQuestion, Review, ReviewImage


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 1
    fields = ("image", "thumbnail")
    readonly_fields = ("thumbnail",)

    @admin.display(description="")
    def thumbnail(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" class="admin-thumb">', obj.image.url)
        return "—"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_verified_purchase", "is_approved", "created_at")
    list_filter = ("is_approved", "is_verified_purchase", "rating")
    search_fields = ("product__name", "user__username", "title", "body")
    date_hierarchy = "created_at"
    inlines = [ReviewImageInline]
    actions = ["approve_reviews", "reject_reviews"]

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Reject selected reviews")
    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)


class ProductAnswerInline(admin.TabularInline):
    model = ProductAnswer
    extra = 1


@admin.register(ProductQuestion)
class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "question", "created_at")
    search_fields = ("product__name", "question")
    inlines = [ProductAnswerInline]
