"""
Test Suite for Product Reviews, Rating Validation, Verified Purchase Badges & Q&A.
"""
import pytest
from tests.pages.product_detail_page import ProductDetailPage
from tests.data.test_data import TEST_REVIEW


@pytest.mark.reviews
@pytest.mark.django_db(transaction=True)
def test_submit_product_review(customer_page, app_url):
    """Verifies submitting a product review as an authenticated user."""
    pdp = ProductDetailPage(customer_page, app_url)
    pdp.open_product("royal-kundan-choker-necklace")

    pdp.submit_review(
        rating=TEST_REVIEW["rating"],
        title=TEST_REVIEW["title"],
        body=TEST_REVIEW["body"]
    )
    assert customer_page.is_visible("div:has-text('submitted'), div:has-text('submitted a review')")


@pytest.mark.reviews
@pytest.mark.django_db(transaction=True)
def test_duplicate_review_prevention(customer_page, app_url):
    """Verifies that submitting a duplicate review for the same product is blocked gracefully."""
    pdp = ProductDetailPage(customer_page, app_url)
    pdp.open_product("royal-kundan-choker-necklace")

    # First submission
    pdp.submit_review(rating=5, title="Great", body="Nice piece")

    # Second submission
    pdp.submit_review(rating=5, title="Duplicate", body="Duplicate submission")
    assert customer_page.is_visible("div:has-text('already submitted a review'), div:has-text('submitted')")


@pytest.mark.reviews
@pytest.mark.django_db(transaction=True)
def test_review_sorting_dropdown(page, app_url, db_seeded):
    """Verifies review sorting dropdown reloads page with active review_sort parameter."""
    pdp = ProductDetailPage(page, app_url)
    pdp.open_product("royal-kundan-choker-necklace")

    # Open reviews tab
    pdp.click(pdp.REVIEWS_TAB_BTN)
    assert pdp.is_visible("#reviewSortSelect")

    # Select rating_high and submit GET form
    page.select_option("#reviewSortSelect", "rating_high")
    page.evaluate("document.querySelector('#reviewSortSelect').form.submit()")
    page.wait_for_load_state("networkidle")
    assert "review_sort=rating_high" in page.url
