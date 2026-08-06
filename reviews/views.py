from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from catalog.models import Product
from .models import ProductQuestion, Review


from orders.models import Order, OrderItem


class AddReviewView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)

        try:
            rating_val = int(request.POST.get("rating", 5))
            if not (1 <= rating_val <= 5):
                raise ValueError()
        except (ValueError, TypeError):
            messages.error(request, "Please select a valid rating between 1 and 5 stars.")
            return redirect(product.get_absolute_url())

        # Fallback check for duplicate review by user
        if Review.objects.filter(product=product, user=request.user).exists():
            messages.error(request, "You have already submitted a review for this product.")
            return redirect(product.get_absolute_url())

        # Check for delivered purchase to verify
        matching_order_item = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status=Order.Status.DELIVERED
        ).first()

        Review.objects.create(
            product=product,
            user=request.user,
            order_item=matching_order_item,
            rating=rating_val,
            title=request.POST.get("title", "").strip(),
            body=request.POST.get("body", "").strip(),
            is_verified_purchase=bool(matching_order_item),
        )
        # Recalculate average_rating and review_count
        approved_reviews = product.reviews.filter(is_approved=True)
        stats = approved_reviews.aggregate(avg=Avg("rating"), count=Count("id"))
        product.average_rating = round(stats["avg"] or 0, 2)
        product.review_count = stats["count"] or 0
        product.save(update_fields=["average_rating", "review_count"])

        messages.success(request, "Thank you! Your review has been submitted.")
        return redirect(product.get_absolute_url())


class AskQuestionView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        ProductQuestion.objects.create(
            product=product, user=request.user, question=request.POST.get("question", "")
        )
        return redirect(product.get_absolute_url())
