"""
Page Object Model for EternaAura Catalog, Search, and Category Listing pages.
"""
from tests.pages.base_page import BasePage


class CatalogPage(BasePage):
    # Locators
    PAGE_HEADER = "h1"
    PRODUCT_CARDS = "article, .group, [data-product-card]"
    SORT_SELECT = "select[name='sort']"
    PRICE_MIN_INPUT = "input[name='min_price']"
    PRICE_MAX_INPUT = "input[name='max_price']"
    FILTER_SUBMIT = "button[type='submit']:has-text('Filter')"
    PURITY_CHECKBOX = "input[name='purity']"

    def open_category(self, slug: str):
        return self.navigate(f"/category/{slug}/")

    def open_collection(self, slug: str):
        return self.navigate(f"/collection/{slug}/")

    def open_new_arrivals(self):
        return self.navigate("/new-arrivals/")

    def open_best_sellers(self):
        return self.navigate("/best-sellers/")

    def open_trending(self):
        return self.navigate("/trending-collections/")

    def get_product_count(self) -> int:
        return self.page.locator(self.PRODUCT_CARDS).count()

    def click_first_product(self):
        self.page.locator(self.PRODUCT_CARDS).first.click()
        self.page.wait_for_load_state("networkidle")
