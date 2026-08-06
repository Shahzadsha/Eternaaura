from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Percentage"
        FLAT = "flat", "Flat amount"

    code = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=200, blank=True)
    discount_type = models.CharField(max_length=10, choices=DiscountType.choices, default=DiscountType.PERCENT)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    user_limit = models.PositiveIntegerField(default=1, help_text="Maximum times a single user can redeem this coupon")
    times_used = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def is_valid_now(self, user=None):
        now = timezone.now()
        if not self.is_active or not (self.valid_from <= now <= self.valid_until):
            return False
        if self.usage_limit is not None and self.times_used >= self.usage_limit:
            return False
        if user and user.is_authenticated:
            from orders.models import Order
            user_used_count = Order.objects.filter(user=user, coupon=self).count()
            if self.user_limit is not None and user_used_count >= self.user_limit:
                return False
        return True

    def calculate_discount(self, order_total):
        if self.discount_type == self.DiscountType.PERCENT:
            amount = order_total * (self.discount_value / 100)
        else:
            amount = self.discount_value
        if self.max_discount_amount:
            amount = min(amount, self.max_discount_amount)
        return min(amount, order_total)

    def __str__(self):
        return self.code
