from django.conf import settings
from django.db import models


class Review(models.Model):
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    order_item = models.ForeignKey("orders.OrderItem", on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=150, blank=True)
    body = models.TextField(blank=True)
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "user", "order_item")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} — {self.rating}★ by {self.user}"


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="reviews/")


class ProductQuestion(models.Model):
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="questions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)


class ProductAnswer(models.Model):
    question = models.ForeignKey(ProductQuestion, on_delete=models.CASCADE, related_name="answers")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    answer = models.CharField(max_length=500)
    is_official = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
