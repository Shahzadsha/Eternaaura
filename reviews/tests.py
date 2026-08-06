from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Address
from catalog.models import Category, Product
from orders.models import Order, OrderItem
from reviews.models import Review

User = get_user_model()


class ReviewSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reviewer@eternaaura.com",
            email="reviewer@eternaaura.com",
            password="SecurePassword123!",
            is_active=True,
            is_email_verified=True,
        )
        self.category = Category.objects.create(name="Earrings", slug="earrings")
        self.product = Product.objects.create(
            category=self.category,
            name="Pearl Drop Earrings",
            slug="pearl-drop-earrings",
            sku="ERG-001",
            price=Decimal("8000.00"),
            stock_quantity=10,
            is_published=True,
        )
        self.address = Address.objects.create(
            user=self.user,
            full_name="Reviewer User",
            phone_number="+919876543210",
            line1="789 Pearl Street",
            city="Bangalore",
            state="Karnataka",
            postal_code="560001",
        )

    def test_invalid_rating_input_handles_gracefully(self):
        self.client.login(username="reviewer@eternaaura.com", password="SecurePassword123!")
        add_review_url = reverse("reviews:add", kwargs={"product_id": self.product.id})
        response = self.client.post(add_review_url, {"rating": "invalid_number", "title": "Great", "body": "Nice"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.count(), 0)

    def test_review_verified_purchase_and_duplicate_prevention(self):
        self.client.login(username="reviewer@eternaaura.com", password="SecurePassword123!")

        # Create delivered order
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            status=Order.Status.DELIVERED,
            subtotal=Decimal("8000.00"),
            grand_total=Decimal("8000.00"),
        )
        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name_snapshot=self.product.name,
            unit_price_snapshot=self.product.price,
            quantity=1,
        )

        add_review_url = reverse("reviews:add", kwargs={"product_id": self.product.id})
        res1 = self.client.post(add_review_url, {"rating": 5, "title": "Stunning!", "body": "Loved it."})
        self.assertEqual(res1.status_code, 302)

        review = Review.objects.filter(product=self.product, user=self.user).first()
        self.assertIsNotNone(review)
        self.assertTrue(review.is_verified_purchase)
        self.assertEqual(review.order_item, order_item)

        # Attempt duplicate review
        res2 = self.client.post(add_review_url, {"rating": 5, "title": "Another review", "body": "Duplicate"})
        self.assertEqual(res2.status_code, 302)
        self.assertEqual(Review.objects.filter(product=self.product, user=self.user).count(), 1)
