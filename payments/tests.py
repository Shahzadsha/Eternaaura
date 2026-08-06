from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Address
from catalog.models import Category, Product
from orders.models import Order, OrderItem
from payments.models import Payment

User = get_user_model()


class PaymentFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser@eternaaura.com",
            email="testuser@eternaaura.com",
            password="SecurePassword123!",
            is_active=True,
            is_email_verified=True,
        )
        self.staff_user = User.objects.create_superuser(
            username="staffuser@eternaaura.com",
            email="staffuser@eternaaura.com",
            password="SecurePassword123!",
            is_staff=True,
            is_superuser=True,
        )
        self.category = Category.objects.create(name="Necklaces", slug="necklaces")
        self.product = Product.objects.create(
            category=self.category,
            name="Diamond Pendant",
            slug="diamond-pendant",
            sku="NCK-001",
            price=Decimal("12000.00"),
            stock_quantity=5,
            is_published=True,
        )
        self.address = Address.objects.create(
            user=self.user,
            full_name="Test User",
            phone_number="+919876543210",
            line1="456 Sparkle Street",
            city="Delhi",
            state="Delhi",
            postal_code="110001",
            is_default=True,
        )

    def test_payment_record_and_qr_views(self):
        self.client.login(username="testuser@eternaaura.com", password="SecurePassword123!")

        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            status=Order.Status.PENDING,
            subtotal=Decimal("12000.00"),
            discount_total=Decimal("0.00"),
            shipping_fee=Decimal("0.00"),
            grand_total=Decimal("12000.00"),
        )

        payment = Payment.objects.create(
            order=order,
            gateway=Payment.Gateway.UPI_QR,
            amount=Decimal("12000.00"),
            status=Payment.Status.PENDING_VERIFICATION,
            upi_link="upi://pay?pa=eternaaura@upi&pn=EternaAura&am=12000.00&cu=INR&tr=TRX123456789012&tn=Order_EA123",
        )

        self.assertIsNotNone(payment.transaction_ref)
        self.assertTrue(payment.transaction_ref.startswith("TRX"))

        # Test dynamic QR code view
        qr_url = reverse("payments:upi_qr", kwargs={"payment_id": payment.id})
        qr_res = self.client.get(qr_url)
        self.assertEqual(qr_res.status_code, 200)
        self.assertEqual(qr_res["Content-Type"], "image/png")

        # Test preview QR view
        preview_url = reverse("payments:upi_qr_preview") + "?am=12000.00&tr=TRXPREVIEW123"
        preview_res = self.client.get(preview_url)
        self.assertEqual(preview_res.status_code, 200)
        self.assertEqual(preview_res["Content-Type"], "image/png")

    def test_staff_payment_verification_action(self):
        self.client.login(username="staffuser@eternaaura.com", password="SecurePassword123!")

        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            status=Order.Status.PENDING,
            subtotal=Decimal("12000.00"),
            discount_total=Decimal("0.00"),
            shipping_fee=Decimal("0.00"),
            grand_total=Decimal("12000.00"),
        )
        payment = Payment.objects.create(
            order=order,
            gateway=Payment.Gateway.UPI_QR,
            amount=Decimal("12000.00"),
            status=Payment.Status.PENDING_VERIFICATION,
            upi_link="upi://pay?pa=eternaaura@upi&pn=EternaAura&am=12000.00&cu=INR&tr=TRX999999999999&tn=Order_EA999",
        )

        verify_url = reverse("dashboard:order_verify_payment", kwargs={"pk": order.pk})
        response = self.client.post(verify_url)
        self.assertEqual(response.status_code, 302)

        order.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertEqual(payment.status, Payment.Status.SUCCESS)
