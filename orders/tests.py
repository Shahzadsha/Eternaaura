from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import Address
from cart.models import Cart, CartItem
from catalog.models import Category, Product
from orders.models import Order, OrderItem

User = get_user_model()


class OrdersAndBuyNowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ordercustomer@eternaaura.com",
            email="ordercustomer@eternaaura.com",
            first_name="Customer",
            last_name="Order",
            password="SecurePassword123!",
            is_active=True,
            is_email_verified=True,
        )

        self.category = Category.objects.create(name="Rings", slug="rings")
        self.product1 = Product.objects.create(
            category=self.category,
            name="Solitaire Diamond Ring",
            slug="solitaire-diamond-ring",
            sku="RNG-001",
            price=Decimal("45000.00"),
            stock_quantity=10,
            is_published=True,
        )
        self.product2 = Product.objects.create(
            category=self.category,
            name="Gold Band Ring",
            slug="gold-band-ring",
            sku="RNG-002",
            price=Decimal("15000.00"),
            stock_quantity=5,
            is_published=True,
        )
        self.address = Address.objects.create(
            user=self.user,
            full_name="Customer Order",
            phone_number="+919876543210",
            line1="123 Luxury Avenue",
            city="Mumbai",
            state="Maharashtra",
            postal_code="400001",
            is_default=True,
        )

    def test_buy_now_post_and_checkout_flow(self):
        self.client.login(username="ordercustomer@eternaaura.com", password="SecurePassword123!")

        # 1. Add product2 to regular Cart
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=1)
        self.assertEqual(cart.items.count(), 1)

        # 2. Trigger Buy Now on product1 (quantity=2)
        buy_now_url = reverse("orders:buy_now", kwargs={"product_id": self.product1.id})
        response = self.client.post(buy_now_url, {"quantity": 2})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("orders:checkout"))

        # Verify Buy Now session payload
        self.assertEqual(
            self.client.session.get("buy_now_session"),
            {"product_id": str(self.product1.id), "quantity": 2},
        )

        # 3. View Checkout page (should calculate subtotal for product1 x 2 = 90,000)
        checkout_res = self.client.get(reverse("orders:checkout"))
        self.assertEqual(checkout_res.status_code, 200)

        # 4. Place Order via Checkout POST
        place_order_res = self.client.post(
            reverse("orders:checkout"),
            {
                "payment_completed": "yes",
                "address_id": self.address.id,
            },
        )
        self.assertEqual(place_order_res.status_code, 302)

        # 5. Verify Order Creation and Cart Isolation
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.product, self.product1)
        self.assertEqual(item.quantity, 2)

        # Stock deducted on product1 (10 - 2 = 8)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock_quantity, 8)

        # Regular cart item (product2) remains completely untouched!
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 1)

