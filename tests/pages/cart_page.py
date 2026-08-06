"""
Page Object Model for EternaAura Cart Page.
"""
from tests.pages.base_page import BasePage


class CartPage(BasePage):
    CART_TITLE = "main h1:has-text('Shopping Cart')"
    COUPON_INPUT = "main form[action*='coupons/apply'] input[name='code']"
    COUPON_APPLY_BTN = "main form[action*='coupons/apply'] button"
    REMOVE_COUPON_BTN = "main form[action*='coupons/remove'] button"
    CHECKOUT_BTN = "main a[href*='orders/checkout']"

    def open(self):
        return self.navigate("/cart/")

    def apply_coupon(self, code: str):
        self.fill(self.COUPON_INPUT, code)
        self.click(self.COUPON_APPLY_BTN)
        self.page.wait_for_load_state("networkidle")

    def proceed_to_checkout(self):
        self.click(self.CHECKOUT_BTN)
        self.page.wait_for_load_state("networkidle")
