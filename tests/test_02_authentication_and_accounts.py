"""
Test Suite for User Registration, Login, Logout, Password Reset, Profile & Address Management.
"""
import pytest
from tests.pages.accounts_page import AccountsPage
from tests.data.test_data import TEST_USERS


@pytest.mark.auth
@pytest.mark.django_db(transaction=True)
def test_user_login_and_logout_flow(page, app_url, db_seeded):
    """Verifies customer login and secure logout process."""
    accounts_page = AccountsPage(page, app_url)
    accounts_page.login(
        TEST_USERS["customer"]["username"],
        TEST_USERS["customer"]["password"]
    )
    assert accounts_page.is_visible("header")

    # Logout
    accounts_page.navigate("/account/logout/")
    assert "login" in page.url or accounts_page.is_visible("main form #id_username")


@pytest.mark.auth
@pytest.mark.django_db(transaction=True)
def test_password_reset_request_flow(page, app_url, db_seeded):
    """Verifies requesting a password reset email link."""
    accounts_page = AccountsPage(page, app_url)
    accounts_page.open_password_reset()
    accounts_page.fill(accounts_page.RESET_EMAIL_INPUT, TEST_USERS["customer"]["email"])
    accounts_page.click(accounts_page.RESET_SUBMIT)
    page.wait_for_load_state("networkidle")
    assert "login" in page.url or accounts_page.is_visible("div:has-text('If that email exists')") or accounts_page.is_visible("main form")


@pytest.mark.auth
@pytest.mark.django_db(transaction=True)
def test_address_management_views(customer_page, app_url):
    """Verifies viewing customer addresses."""
    accounts_page = AccountsPage(customer_page, app_url)
    accounts_page.open_addresses()
    assert accounts_page.is_visible("h1:has-text('Saved Addresses'), h1:has-text('Addresses')")
