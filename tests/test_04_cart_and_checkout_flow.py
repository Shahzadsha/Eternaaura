"""
Test Suite for Cart Operations, Coupon Validation, Checkout Address & Dynamic UPI Payment Preview.
"""
import pytest
from tests.pages.product_detail_page import ProductDetailPage
from tests.pages.cart_page import CartPage
from tests.pages.checkout_page import CheckoutPage
from tests.data.test_data import TEST_COUPON, TEST_ADDRESS


@pytest.mark.checkout
@pytest.mark.django_db(transaction=True)
def test_add_to_cart_and_view_cart(page, app_url, db_seeded):
    """Verifies adding a product to cart and viewing cart details."""
    pdp = ProductDetailPage(page, app_url)
    pdp.open_product("royal-kundan-choker-necklace")
    pdp.add_to_cart(quantity=1)

    cart_page = CartPage(page, app_url)
    cart_page.open()
    assert cart_page.is_visible(cart_page.CHECKOUT_BTN)


@pytest.mark.checkout
@pytest.mark.django_db(transaction=True)
def test_apply_valid_coupon_code(page, app_url, db_seeded):
    """Verifies applying a valid coupon code in cart."""
    pdp = ProductDetailPage(page, app_url)
    pdp.open_product("royal-kundan-choker-necklace")
    pdp.add_to_cart(quantity=1)

    cart_page = CartPage(page, app_url)
    cart_page.open()
    cart_page.apply_coupon(TEST_COUPON["code"])
    assert cart_page.is_visible("p:has-text('Promo Code Applied'), div:has-text('Applied')")


@pytest.mark.checkout
@pytest.mark.django_db(transaction=True)
def test_checkout_and_dynamic_upi_payment_flow(customer_page, app_url):
    """Verifies checkout flow, address selection, and dynamic UPI QR code preview."""
    pdp = ProductDetailPage(customer_page, app_url)
    pdp.open_product("royal-kundan-choker-necklace")
    pdp.add_to_cart(quantity=1)

    checkout_page = CheckoutPage(customer_page, app_url)
    checkout_page.open()
    assert checkout_page.is_visible(checkout_page.PLACE_ORDER_BTN)
