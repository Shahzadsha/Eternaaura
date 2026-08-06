from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from catalog.models import Category, Product, Wishlist

User = get_user_model()


class CatalogFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="catalogcustomer@eternaaura.com",
            email="catalogcustomer@eternaaura.com",
            first_name="Customer",
            last_name="Catalog",
            password="SecurePassword123!",
            is_active=True,
            is_email_verified=True,
        )

        self.category = Category.objects.create(name="Earrings", slug="earrings")
        self.product = Product.objects.create(
            category=self.category,
            name="Pearl Drop Earrings",
            slug="pearl-drop-earrings",
            sku="EAR-001",
            price=Decimal("12000.00"),
            stock_quantity=8,
            is_published=True,
            is_new_arrival=True,
            is_best_seller=True,
            is_trending=True,
        )

    def test_showcase_standalone_pages(self):
        # New Arrivals page
        res1 = self.client.get(reverse("catalog:new_arrivals"))
        self.assertEqual(res1.status_code, 200)
        self.assertContains(res1, "Pearl Drop Earrings")

        # Best Sellers page
        res2 = self.client.get(reverse("catalog:best_sellers"))
        self.assertEqual(res2.status_code, 200)
        self.assertContains(res2, "Pearl Drop Earrings")

        # Trending Collections page
        res3 = self.client.get(reverse("catalog:trending"))
        self.assertEqual(res3.status_code, 200)
        self.assertContains(res3, "Pearl Drop Earrings")

    def test_ajax_wishlist_toggle(self):
        url = reverse("catalog:toggle_wishlist", kwargs={"product_id": self.product.id})

        # Unauthenticated AJAX request -> 401 JSON redirect
        res_unauth = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res_unauth.status_code, 401)

        # Authenticated AJAX request -> toggle ON
        self.client.login(username="catalogcustomer@eternaaura.com", password="SecurePassword123!")
        res_on = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res_on.status_code, 200)
        self.assertEqual(res_on.json()["count"], 1)
        self.assertTrue(res_on.json()["wishlisted"])
        self.assertEqual(Wishlist.objects.filter(user=self.user).count(), 1)

        # Authenticated AJAX request -> toggle OFF
        res_off = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res_off.status_code, 200)
        self.assertEqual(res_off.json()["count"], 0)
        self.assertFalse(res_off.json()["wishlisted"])
        self.assertEqual(Wishlist.objects.filter(user=self.user).count(), 0)

