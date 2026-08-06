"""
Page Object Model for EternaAura Checkout & Payment Flow Page.
"""
from tests.pages.base_page import BasePage


class CheckoutPage(BasePage):
    PAGE_TITLE = "h1:has-text('Checkout')"
    ADDRESS_RADIO = "main form input[name='address_id']"
    FULL_NAME_INPUT = "main form input[name='full_name']"
    PHONE_INPUT = "main form input[name='phone_number']"
    LINE1_INPUT = "main form input[name='line1']"
    LINE2_INPUT = "main form input[name='line2']"
    CITY_INPUT = "main form input[name='city']"
    STATE_INPUT = "main form input[name='state']"
    POSTAL_CODE_INPUT = "main form input[name='postal_code']"
    PAYMENT_COMPLETED_CHECKBOX = "#payment_completed, main form input[name='payment_completed']"
    PLACE_ORDER_BTN = "#place_order_btn, main form button[type='submit']"

    def open(self):
        return self.navigate("/orders/checkout/")

    def select_first_saved_address(self):
        if self.is_visible(self.ADDRESS_RADIO):
            self.page.locator(self.ADDRESS_RADIO).first.check()

    def fill_new_address(self, data: dict):
        self.fill(self.FULL_NAME_INPUT, data["full_name"])
        self.fill(self.PHONE_INPUT, data["phone_number"])
        self.fill(self.LINE1_INPUT, data["line1"])
        if "line2" in data and self.is_visible(self.LINE2_INPUT):
            self.fill(self.LINE2_INPUT, data["line2"])
        self.fill(self.CITY_INPUT, data["city"])
        self.fill(self.STATE_INPUT, data["state"])
        self.fill(self.POSTAL_CODE_INPUT, data["postal_code"])

    def confirm_payment_completed(self):
        if self.is_visible(self.PAYMENT_COMPLETED_CHECKBOX):
            self.page.check(self.PAYMENT_COMPLETED_CHECKBOX)

    def place_order(self):
        self.confirm_payment_completed()
        self.click(self.PLACE_ORDER_BTN)
        self.page.wait_for_load_state("networkidle")
