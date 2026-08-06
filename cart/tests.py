from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product
from cart.models import Cart

User = get_user_model()


class CartSecurityTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Bracelets", slug="bracelets")
        self.published_product = Product.objects.create(
            category=self.category,
            name="Gold Bangle",
            slug="gold-bangle",
            sku="BNG-001",
            price=Decimal("25000.00"),
            stock_quantity=10,
            is_published=True,
        )
        self.draft_product = Product.objects.create(
            category=self.category,
            name="Unpublished Prototype Bangle",
            slug="prototype-bangle",
            sku="BNG-002",
            price=Decimal("50000.00"),
            stock_quantity=1,
            is_published=False,
        )

    def test_add_published_product_to_cart(self):
        add_url = reverse("cart:add", kwargs={"product_id": self.published_product.id})
        response = self.client.post(add_url, {"quantity": 1})
        self.assertEqual(response.status_code, 302)

    def test_add_draft_product_to_cart_returns_404(self):
        add_url = reverse("cart:add", kwargs={"product_id": self.draft_product.id})
        response = self.client.post(add_url, {"quantity": 1})
        self.assertEqual(response.status_code, 404)
