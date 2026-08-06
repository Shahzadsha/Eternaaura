"""
Page Object Model for EternaAura Product Detail Page (PDP) using strict, semantic locators.
"""
from tests.pages.base_page import BasePage


class ProductDetailPage(BasePage):
    PRODUCT_TITLE = "h1"
    PRODUCT_PRICE = "div:has-text('₹')"
    STOCK_BADGE = "span:has-text('In Stock'), span:has-text('Out of Stock')"
    QUANTITY_INPUT = "main input[name='quantity']"
    ADD_TO_CART_BTN = "main form[action*='cart/add'] button:has-text('Add to Cart')"
    BUY_NOW_BTN = "main form[action*='orders/buy-now'] button:has-text('Buy Now')"
    WISHLIST_BTN = "main button[aria-label='Toggle Wishlist']"

    # Review Locators
    REVIEWS_TAB_BTN = "button:has-text('Reviews')"
    REVIEW_RATING_SELECT = "main form[action*='reviews'] select[name='rating']"
    REVIEW_TITLE_INPUT = "main form[action*='reviews'] input[name='title']"
    REVIEW_BODY_TEXTAREA = "main form[action*='reviews'] textarea[name='body']"
    REVIEW_SUBMIT_BTN = "main form[action*='reviews'] button:has-text('Submit Review')"

    def open_product(self, slug: str):
        return self.navigate(f"/product/{slug}/")

    def add_to_cart(self, quantity: int = 1):
        if self.is_visible(self.QUANTITY_INPUT):
            self.fill(self.QUANTITY_INPUT, str(quantity))
        self.click(self.ADD_TO_CART_BTN)
        self.page.wait_for_load_state("networkidle")

    def click_buy_now(self):
        self.click(self.BUY_NOW_BTN)
        self.page.wait_for_load_state("networkidle")

    def toggle_wishlist(self):
        self.click(self.WISHLIST_BTN)
        self.page.wait_for_load_state("networkidle")

    def submit_review(self, rating: int, title: str, body: str):
        if self.is_visible(self.REVIEWS_TAB_BTN):
            self.click(self.REVIEWS_TAB_BTN)
        if self.is_visible(self.REVIEW_RATING_SELECT):
            self.page.select_option(self.REVIEW_RATING_SELECT, str(rating))
        if self.is_visible(self.REVIEW_TITLE_INPUT):
            self.fill(self.REVIEW_TITLE_INPUT, title)
        if self.is_visible(self.REVIEW_BODY_TEXTAREA):
            self.fill(self.REVIEW_BODY_TEXTAREA, body)
        self.click(self.REVIEW_SUBMIT_BTN)
        self.page.wait_for_load_state("networkidle")
