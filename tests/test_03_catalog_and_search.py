"""
Test Suite for Home Page, Catalog Browsing, Search, Filters, Product Detail & Wishlist.
"""
import pytest
from tests.pages.home_page import HomePage
from tests.pages.catalog_page import CatalogPage
from tests.pages.product_detail_page import ProductDetailPage


@pytest.mark.catalog
@pytest.mark.django_db(transaction=True)
def test_home_page_rendering_and_navigation(page, app_url, db_seeded):
    """Verifies home page hero carousel, navigation bar, and footer rendering."""
    home_page = HomePage(page, app_url)
    home_page.open()
    home_page.assert_title_contains("ETERNAAURA")
    assert home_page.is_visible(home_page.NAV_BRAND)


@pytest.mark.catalog
@pytest.mark.django_db(transaction=True)
def test_category_and_search_results(page, app_url, db_seeded):
    """Verifies category listing and search execution."""
    catalog_page = CatalogPage(page, app_url)
    catalog_page.open_category("necklaces")
    assert catalog_page.is_visible("h1:has-text('Necklaces')")

    # Search execution
    home_page = HomePage(page, app_url)
    home_page.open()
    home_page.search_for("Kundan")
    assert "search" in page.url


@pytest.mark.catalog
@pytest.mark.django_db(transaction=True)
def test_product_detail_page_interactions(page, app_url, db_seeded):
    """Verifies product detail page elements and stock badge."""
    pdp = ProductDetailPage(page, app_url)
    pdp.open_product("royal-kundan-choker-necklace")
    assert pdp.is_visible(pdp.PRODUCT_TITLE)
    assert pdp.is_visible(pdp.ADD_TO_CART_BTN)


@pytest.mark.catalog
@pytest.mark.django_db(transaction=True)
def test_category_sorting_and_wishlist_ajax_toggle(customer_page, app_url, db_seeded):
    """Verifies category sorting selector and wishlist form toggling."""
    catalog_page = CatalogPage(customer_page, app_url)
    catalog_page.open_category("necklaces")
    assert catalog_page.is_visible("#sortSelect")

    # Select price_high sorting and submit GET form
    customer_page.select_option("#sortSelect", "price_high")
    customer_page.evaluate("document.querySelector('#sortSelect').form.submit()")
    customer_page.wait_for_load_state("networkidle")
    assert "sort=price_high" in customer_page.url

    # Toggle Wishlist
    wishlist_btn = customer_page.locator("button[aria-label='Toggle Wishlist']").first
    wishlist_btn.click()
    customer_page.wait_for_load_state("networkidle")
    assert customer_page.is_visible("[data-wishlist-count-badge]")
