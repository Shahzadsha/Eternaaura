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


class ProductBrandRepositioningPropertiesTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Earrings", slug="earrings")
        self.gift_category = Category.objects.create(name="Gift Sets & Hampers", slug="gift-sets-hampers")
        self.collection = Collection.objects.create(name="Gifting & Festive Hampers", slug="gifting-festive-hampers")

    def test_is_anti_tarnish_property(self):
        # 1. Explicit affirmative values
        p1 = Product(specifications={"Anti-Tarnish": "Yes"})
        self.assertTrue(p1.is_anti_tarnish)

        p2 = Product(specifications={"anti_tarnish": "true"})
        self.assertTrue(p2.is_anti_tarnish)

        p3 = Product(specifications={"Anti Tarnish": "1"})
        self.assertTrue(p3.is_anti_tarnish)

        # 2. Negative or missing values
        p4 = Product(specifications={"Anti-Tarnish": "No"})
        self.assertFalse(p4.is_anti_tarnish)

        p5 = Product(specifications={})
        self.assertFalse(p5.is_anti_tarnish)

        p6 = Product(specifications=None)
        self.assertFalse(p6.is_anti_tarnish)

    def test_price_tier_properties(self):
        p1 = Product(price=Decimal("149.00"))
        self.assertTrue(p1.is_under_199)
        self.assertTrue(p1.is_under_299)

        p2 = Product(price=Decimal("199.00"))
        self.assertTrue(p2.is_under_199)
        self.assertTrue(p2.is_under_299)

        p3 = Product(price=Decimal("249.00"))
        self.assertFalse(p3.is_under_199)
        self.assertTrue(p3.is_under_299)

        p4 = Product(price=Decimal("299.00"))
        self.assertFalse(p4.is_under_199)
        self.assertTrue(p4.is_under_299)

        p5 = Product(price=Decimal("349.00"))
        self.assertFalse(p5.is_under_199)
        self.assertFalse(p5.is_under_299)

    def test_is_gift_pick_property(self):
        # 1. By specifications
        p1 = Product(specifications={"Gift Pick": "Yes"})
        self.assertTrue(p1.is_gift_pick)

        p2 = Product(specifications={"Occasion": "Festive Gift Hamper"})
        self.assertTrue(p2.is_gift_pick)

        # 2. By category (in-memory)
        p3 = Product(category=self.gift_category)
        self.assertTrue(p3.is_gift_pick)

        # 3. Standard piece
        p4 = Product(category=self.category, specifications={"Material": "Brass"})
        self.assertFalse(p4.is_gift_pick)

    def test_is_anti_tarnish_never_infers_from_other_fields(self):
        # Even if product name, description, or category has "Anti-Tarnish", property must NOT infer it
        p = Product.objects.create(
            category=self.category,
            name="Anti-Tarnish Golden Ring",
            slug="anti-tarnish-golden-ring",
            sku="AT-RNG-01",
            price=Decimal("199.00"),
            description="Our best waterproof anti-tarnish daily wear ring.",
            specifications={},  # No explicit anti-tarnish spec
        )
        self.assertFalse(p.is_anti_tarnish)

    def test_is_gift_pick_performs_zero_queries_when_unfetched(self):
        p = Product.objects.create(
            category=self.category,
            name="Standard Daily Ring",
            slug="standard-daily-ring",
            sku="SDR-01",
            price=Decimal("199.00"),
            specifications={},
        )
        # Fetch from DB without select_related / prefetch_related
        raw_product = Product.objects.only("id", "name", "price", "specifications").get(id=p.id)

        # Accessing is_gift_pick must emit strictly ZERO database queries
        with self.assertNumQueries(0):
            result = raw_product.is_gift_pick
            self.assertFalse(result)

    def test_is_gift_pick_with_prefetched_collections(self):
        p = Product.objects.create(
            category=self.category,
            name="Festive Gift Box",
            slug="festive-gift-box",
            sku="FGB-01",
            price=Decimal("499.00"),
            specifications={},
        )
        self.collection.products.add(p)

        # Fetch with prefetch_related
        prefetched_product = Product.objects.prefetch_related("collections").get(id=p.id)

        # Must evaluate to True using _prefetched_objects_cache without extra queries
        with self.assertNumQueries(0):
            self.assertTrue(prefetched_product.is_gift_pick)

    def test_badge_rendering_and_zero_n_plus_one_queries(self):
        # Create 10 test products
        for i in range(10):
            p = Product.objects.create(
                category=self.category,
                name=f"Trendy Hoop #{i}",
                slug=f"trendy-hoop-{i}",
                sku=f"THP-00{i}",
                price=Decimal("149.00" if i % 2 == 0 else "249.00"),
                stock_quantity=10,
                is_published=True,
                is_new_arrival=True,
                is_best_seller=(i % 2 == 0),
                specifications={"Anti-Tarnish": "Yes"} if i % 2 == 0 else {},
            )
            ProductImage.objects.create(product=p, display_order=1)

        # Ensure Category page renders and contains badges
        res_cat = self.client.get(reverse("catalog:category_detail", kwargs={"slug": self.category.slug}))
        self.assertEqual(res_cat.status_code, 200)
        self.assertContains(res_cat, "Anti-Tarnish")
        self.assertContains(res_cat, "Under ₹199")

        # Ensure New Arrivals page renders
        res_new = self.client.get(reverse("catalog:new_arrivals"))
        self.assertEqual(res_new.status_code, 200)
        self.assertContains(res_new, "Trendy Hoop #0")



