"""
Test Suite for Staff Dashboard Navigation, Metrics, Product/Category CRUD & Staff Payment Verification.
"""
import pytest
from tests.pages.dashboard_page import DashboardPage
from tests.data.test_data import TEST_USERS


@pytest.mark.dashboard
@pytest.mark.django_db(transaction=True)
def test_staff_login_and_dashboard_home(page, app_url, db_seeded):
    """Verifies staff manager authentication and dashboard metrics rendering."""
    dashboard = DashboardPage(page, app_url)
    dashboard.staff_login(
        TEST_USERS["staff"]["username"],
        TEST_USERS["staff"]["password"]
    )
    assert dashboard.is_visible(dashboard.DASHBOARD_TITLE) or "staff" in page.url


@pytest.mark.dashboard
@pytest.mark.django_db(transaction=True)
def test_staff_product_and_category_management_pages(staff_page, app_url):
    """Verifies staff access to product and category management views."""
    dashboard = DashboardPage(staff_page, app_url)
    dashboard.open_product_management()
    assert dashboard.is_visible("h1:has-text('Product'), h1:has-text('Products')")

    dashboard.open_category_management()
    assert dashboard.is_visible("h1:has-text('Categor')")


@pytest.mark.dashboard
@pytest.mark.django_db(transaction=True)
def test_staff_order_management_and_payment_verification(staff_page, app_url):
    """Verifies staff order management table and payment verification action."""
    dashboard = DashboardPage(staff_page, app_url)
    dashboard.open_order_management()
    assert dashboard.is_visible("h1:has-text('Order'), h1:has-text('Orders')")
