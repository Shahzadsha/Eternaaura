from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from catalog.models import Category, Collection, HeroBanner, Product, ProductImage, Wishlist


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


class HomeViewPerformanceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="testperfuser@example.com",
            email="testperfuser@example.com",
            password="TestPassword123!",
            is_active=True,
        )

        self.category = Category.objects.create(
            name="Rings", slug="rings", is_active=True, display_order=1
        )
        self.collection1 = Collection.objects.create(
            name="Bridal Collection", slug="bridal-collection", is_active=True
        )
        self.collection2 = Collection.objects.create(
            name="Daily Wear Collection", slug="daily-wear-collection", is_active=True
        )

        self.banner = HeroBanner.objects.create(
            title="Luxury Gold", is_active=True, display_order=1
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Gold Diamond Ring",
            slug="gold-diamond-ring",
            sku="RNG-001",
            price=Decimal("25000.00"),
            stock_quantity=10,
            is_published=True,
            is_new_arrival=True,
            is_best_seller=True,
            is_trending=True,
        )
        self.product_image = ProductImage.objects.create(
            product=self.product, alt_text="Ring view", display_order=1
        )

    def test_homepage_query_count_anonymous_and_authenticated(self):
        cache.clear()

        # Cold cache request (anonymous)
        res_cold = self.client.get(reverse("catalog:home"))
        self.assertEqual(res_cold.status_code, 200)
        self.assertIn("homepage_public_data", cache)

        # Warm cache request (anonymous) -> expect ZERO queries
        with self.assertNumQueries(0):  # type: ignore[attr-defined]
            res_warm = self.client.get(reverse("catalog:home"))
            self.assertEqual(res_warm.status_code, 200)

        # Warm cache request (authenticated) -> expect 4 queries (Session + User + Cart + Wishlist, 0 public data queries)
        self.client.force_login(self.user)
        with self.assertNumQueries(4):  # type: ignore[attr-defined]
            res_auth = self.client.get(reverse("catalog:home"))
            self.assertEqual(res_auth.status_code, 200)




    def test_bridal_and_daily_wear_derivation_and_fallbacks(self):
        cache.clear()

        # Case 1: Standard matching slugs
        res = self.client.get(reverse("catalog:home"))
        self.assertEqual(res.context["bridal"].slug, "bridal-collection")
        self.assertEqual(res.context["daily_wear"].slug, "daily-wear-collection")

        # Case 2: Custom slugs (no bridal-collection / daily-wear-collection)
        cache.clear()
        Collection.objects.all().delete()
        c1 = Collection.objects.create(name="Summer Glow", slug="summer-glow", is_active=True)
        c2 = Collection.objects.create(name="Winter Elegance", slug="winter-elegance", is_active=True)

        res2 = self.client.get(reverse("catalog:home"))
        self.assertEqual(res2.context["bridal"], c1)
        self.assertEqual(res2.context["daily_wear"], c2)

        # Case 3: Single active collection
        cache.clear()
        c2.delete()
        res3 = self.client.get(reverse("catalog:home"))
        self.assertEqual(res3.context["bridal"], c1)
        self.assertIsNone(res3.context["daily_wear"])

        # Case 4: Zero active collections
        cache.clear()
        c1.delete()
        res4 = self.client.get(reverse("catalog:home"))
        self.assertIsNone(res4.context["bridal"])
        self.assertIsNone(res4.context["daily_wear"])
        self.assertEqual(res4.context["collections"], [])

    def test_cache_invalidation_on_model_changes(self):
        # Warm the cache
        self.client.get(reverse("catalog:home"))
        self.assertIsNotNone(cache.get("homepage_public_data"))

        # Save new HeroBanner -> invalidates homepage_public_data
        HeroBanner.objects.create(title="Summer Sale", is_active=True)
        self.assertIsNone(cache.get("homepage_public_data"))

        # Warm again
        self.client.get(reverse("catalog:home"))
        self.assertIsNotNone(cache.get("homepage_public_data"))

        # Update product -> invalidates homepage_public_data
        self.product.is_new_arrival = False
        self.product.save()
        self.assertIsNone(cache.get("homepage_public_data"))

        # Warm again
        self.client.get(reverse("catalog:home"))
        self.assertIsNotNone(cache.get("homepage_public_data"))

        # Delete product image -> invalidates homepage_public_data
        self.product_image.delete()
        self.assertIsNone(cache.get("homepage_public_data"))

        # Warm again
        self.client.get(reverse("catalog:home"))
        self.assertIsNotNone(cache.get("homepage_public_data"))

        # Update collection -> invalidates homepage_public_data & nav_categories_data
        self.collection1.name = "Updated Collection"
        self.collection1.save()
        self.assertIsNone(cache.get("homepage_public_data"))
        self.assertIsNone(cache.get("nav_categories_data"))

    def test_user_privacy_and_context_isolation(self):
        from cart.models import Cart, CartItem
        # User 1 adds item to cart
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=3)

        self.client.force_login(self.user)
        res_user1 = self.client.get(reverse("catalog:home"))
        self.assertEqual(res_user1.context["cart_item_count"], 3)

        # Anonymous user response must have 0 cart items
        self.client.logout()
        res_anon = self.client.get(reverse("catalog:home"))
        self.assertEqual(res_anon.context["cart_item_count"], 0)


