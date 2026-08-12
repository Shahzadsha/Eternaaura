"""
Unit tests for order pricing calculation, COD removal, and button duplicate fixes.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Address
from catalog.models import Category, Product
from coupons.models import Coupon
from dashboard.models import StoreSettings
from orders.models import Order, OrderItem
from payments.models import Payment

User = get_user_model()


class OrderFlowFixesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testcustomer",
            email="testcustomer@example.com",
            password="Password123!",
            is_active=True,
            is_email_verified=True,
        )

        self.address = Address.objects.create(
            user=self.user,
            full_name="Test Customer",
            phone_number="9876543210",
            line1="123 Luxury Lane",
            city="Mumbai",
            state="Maharashtra",
            postal_code="400001",
            country="India",
        )

        self.category = Category.objects.create(name="Rings", slug="rings")
        self.product = Product.objects.create(
            category=self.category,
            name="Diamond Solitaire Ring",
            slug="diamond-solitaire-ring",
            price=Decimal("1200.00"),
            stock_quantity=10,
            is_published=True,
        )

        # Explicitly configure StoreSettings shipping rules
        self.store_settings = StoreSettings.get_solo()
        self.store_settings.standard_shipping_fee = Decimal("150.00")
        self.store_settings.free_shipping_threshold = Decimal("5000.00")
        self.store_settings.merchant_upi_id = "testmerchant@upi"
        self.store_settings.merchant_name = "ETERNAAURA Store"
        self.store_settings.whatsapp_notify_number = "919876543210"
        self.store_settings.save()

    def test_order_creation_standard_shipping(self):
        """Test order creation below free shipping threshold (₹1200 < ₹5000)."""
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            status=Order.Status.PENDING,
            subtotal=Decimal("1200.00"),
            discount_total=Decimal("0.00"),
            shipping_fee=Decimal("150.00"),
            tax_total=Decimal("0.00"),
            grand_total=Decimal("1350.00"),
        )
        Payment.objects.create(
            order=order,
            gateway=Payment.Gateway.UPI_QR,
            amount=Decimal("1350.00"),
            status=Payment.Status.PENDING_VERIFICATION,
        )

        self.assertEqual(order.shipping_fee, Decimal("150.00"))
        self.assertEqual(order.grand_total, Decimal("1350.00"))

        # Verify Order Detail page rendering
        self.client.force_login(self.user)
        res = self.client.get(reverse("orders:detail", kwargs={"pk": order.id}))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode()

        # Must NOT contain Cash on Delivery
        self.assertNotIn("Cash on Delivery", content)
        self.assertNotIn("COD", content)
        # Must show UPI QR Code payment gateway & status
        self.assertIn("UPI QR Code", content)
        self.assertIn("Pending Verification", content)

    def test_order_creation_free_shipping(self):
        """Test order creation above free shipping threshold (₹6000 >= ₹5000)."""
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            status=Order.Status.CONFIRMED,
            subtotal=Decimal("6000.00"),
            discount_total=Decimal("0.00"),
            shipping_fee=Decimal("0.00"),
            tax_total=Decimal("0.00"),
            grand_total=Decimal("6000.00"),
        )
        Payment.objects.create(
            order=order,
            gateway=Payment.Gateway.UPI_QR,
            amount=Decimal("6000.00"),
            status=Payment.Status.SUCCESS,
        )

        self.assertEqual(order.shipping_fee, Decimal("0.00"))
        self.assertEqual(order.grand_total, Decimal("6000.00"))

        self.client.force_login(self.user)
        res = self.client.get(reverse("orders:detail", kwargs={"pk": order.id}))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode()

        self.assertIn("FREE", content)
        self.assertNotIn("Cash on Delivery", content)

    def test_single_view_details_button_on_my_orders_page(self):
        """Test that My Orders page renders exactly 1 'View Details' button per order card."""
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            status=Order.Status.CONFIRMED,
            subtotal=Decimal("1200.00"),
            discount_total=Decimal("0.00"),
            shipping_fee=Decimal("150.00"),
            tax_total=Decimal("0.00"),
            grand_total=Decimal("1350.00"),
        )

        self.client.force_login(self.user)
        res = self.client.get(reverse("orders:history"))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode()

        # Count occurrences of View Details
        count = content.count("View Details")
        self.assertEqual(count, 1)

    def test_whatsapp_redirect_message_formatting_and_product_image_url(self):
        """Test that checkout redirect URL contains formatted WhatsApp message with product image URL and zero Transaction Ref."""
        from catalog.models import ProductImage
        from cart.models import Cart, CartItem
        import urllib.parse

        # Add image to product
        ProductImage.objects.create(
            product=self.product,
            image="products/diamond-ring.jpg",
            alt_text="Diamond Ring",
        )

        # Create cart item
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)

        self.client.force_login(self.user)
        res = self.client.post(
            reverse("orders:checkout"),
            {"payment_completed": "yes", "address_id": self.address.id},
        )
        self.assertEqual(res.status_code, 302)

        redirect_url = res.url
        self.assertTrue(redirect_url.startswith("https://api.whatsapp.com/send"))
        self.assertIn("phone=919876543210", redirect_url)

        # Parse text payload from query string
        parsed = urllib.parse.urlparse(redirect_url)
        query_params = urllib.parse.parse_qs(parsed.query)
        msg_text = query_params["text"][0]

        # Verify product image is prominently at the top
        self.assertTrue(msg_text.startswith("🖼 *PRODUCT IMAGE*"))
        self.assertIn("products/diamond-ring.jpg", msg_text)

        # Verify professional section headers
        self.assertIn("ETERNAAURA — NEW ORDER PLACED", msg_text)
        self.assertIn("ORDER INFORMATION", msg_text)
        self.assertIn("CUSTOMER DETAILS", msg_text)
        self.assertIn("ORDERED PRODUCTS", msg_text)
        self.assertIn("PAYMENT SUMMARY", msg_text)
        self.assertIn("ORDER NOTE", msg_text)

        # Verify Transaction Ref is COMPLETELY ABSENT
        self.assertNotIn("Transaction Ref", msg_text)
        self.assertNotIn("TRX", msg_text)

