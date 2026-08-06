"""
Page Object Model for the EternaAura Home Page.
"""
from tests.pages.base_page import BasePage


class HomePage(BasePage):
    # Locators
    NAV_BRAND = "header a:has-text('ETERNA')"
    NAV_COLLECTION_LINK = "header a[href*='trending-collections']"
    NAV_NEW_ARRIVALS_LINK = "header a[href*='new-arrivals']"
    NAV_BEST_SELLERS_LINK = "header a[href*='best-sellers']"
    NAV_CART_LINK = "header a[href*='cart']"
    NAV_ACCOUNT_LINK = "header a[href*='account']"
    SEARCH_TOGGLE = "button[aria-label='Search']"
    SEARCH_INPUT = "input[name='q']"
    SEARCH_SUBMIT = "form[action*='search'] button"
    HERO_SLIDE = ".hero-slide"
    FEATURED_CATEGORY_CARD = ".category-card"
    PRODUCT_CARD = "article, .group, [data-product-card]"

    def open(self):
        return self.navigate("/")

    def search_for(self, query: str):
        if self.is_visible(self.SEARCH_TOGGLE):
            self.click(self.SEARCH_TOGGLE)
        self.fill(self.SEARCH_INPUT, query)
        self.click(self.SEARCH_SUBMIT)
        self.page.wait_for_load_state("networkidle")

    def click_cart(self):
        self.click(self.NAV_CART_LINK)

    def click_account(self):
        self.click(self.NAV_ACCOUNT_LINK)
