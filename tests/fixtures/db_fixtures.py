"""
Database seeding helpers for initializing Django test data programmatically.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

from catalog.models import Category, Collection, Product, ProductImage
from coupons.models import Coupon
from accounts.models import Address
from orders.models import Order, OrderItem

User = get_user_model()


def seed_test_database():
    """
    Populates test database with standard users, categories, products,
    coupons, and addresses for Playwright testing.
    """
    # Create Users
    customer, _ = User.objects.get_or_create(
        username="qa_customer@eternaaura.com",
        defaults={
            "email": "qa_customer@eternaaura.com",
            "first_name": "QA",
            "last_name": "Customer",
            "phone_number": "+919876543210",
        }
    )
    customer.is_email_verified = True
    customer.is_active = True
    customer.set_password("CustomerSecurePass123!")
    customer.save()

    staff, _ = User.objects.get_or_create(
        username="qa_staff@eternaaura.com",
        defaults={
            "email": "qa_staff@eternaaura.com",
            "first_name": "QA",
            "last_name": "Staff",
            "phone_number": "+919876543211",
        }
    )
    staff.is_email_verified = True
    staff.is_staff = True
    staff.is_active = True
    staff.staff_role = User.StaffRole.SUPER_ADMIN
    staff.set_password("StaffSecurePass123!")
    staff.save()

    admin, _ = User.objects.get_or_create(
        username="qa_admin@eternaaura.com",
        defaults={
            "email": "qa_admin@eternaaura.com",
            "first_name": "QA",
            "last_name": "SuperAdmin",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        }
    )
    admin.set_password("AdminSecurePass123!")
    admin.save()

    # Create Categories
    necklaces, _ = Category.objects.get_or_create(
        slug="necklaces",
        defaults={"name": "Necklaces", "description": "Royal traditional & modern necklaces."}
    )
    rings, _ = Category.objects.get_or_create(
        slug="rings",
        defaults={"name": "Rings", "description": "Diamond and gold engagement rings."}
    )

    # Create Collections
    bridal, _ = Collection.objects.get_or_create(
        slug="bridal-collection",
        defaults={"name": "Bridal Collection", "description": "Exquisite bridal jewelry pieces."}
    )

    # Create Products
    p1, _ = Product.objects.get_or_create(
        sku="NCK-ROYAL-001",
        defaults={
            "name": "Royal Kundan Choker Necklace",
            "slug": "royal-kundan-choker-necklace",
            "category": necklaces,
            "short_description": "Handcrafted Kundan necklace plated in 22K gold.",
            "description": "Authentic artisan crafted Kundan jewelry.",
            "price": Decimal("15000.00"),
            "compare_at_price": Decimal("18000.00"),
            "stock_quantity": 15,
            "is_featured": True,
            "is_published": True,
        }
    )
    p1.collections.add(bridal)

    p2, _ = Product.objects.get_or_create(
        sku="RNG-SOLITAIRE-001",
        defaults={
            "name": "Solitaire Diamond Ring",
            "slug": "solitaire-diamond-ring",
            "category": rings,
            "short_description": "Sparkling solitaire set in 18K white gold.",
            "price": Decimal("45000.00"),
            "stock_quantity": 5,
            "is_featured": True,
            "is_published": True,
        }
    )

    # Create Coupon
    coupon, _ = Coupon.objects.get_or_create(
        code="QAWELCOME10",
        defaults={
            "description": "QA Test 10% Discount",
            "discount_type": Coupon.DiscountType.PERCENT,
            "discount_value": Decimal("10.00"),
            "min_order_value": Decimal("500.00"),
            "valid_from": timezone.now() - timezone.timedelta(days=1),
            "valid_until": timezone.now() + timezone.timedelta(days=30),
            "is_active": True,
        }
    )

    # Create Customer Address
    address, _ = Address.objects.get_or_create(
        user=customer,
        is_default=True,
        defaults={
            "full_name": "QA Customer",
            "phone_number": "+919876543210",
            "line1": "100 Automation Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "postal_code": "400001",
        }
    )

    return {
        "customer": customer,
        "staff": staff,
        "admin": admin,
        "categories": [necklaces, rings],
        "products": [p1, p2],
        "coupon": coupon,
        "address": address,
    }
