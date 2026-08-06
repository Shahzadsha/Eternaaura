"""
Page Object Model for EternaAura Staff Dashboard & RBAC Management area.
"""
from tests.pages.base_page import BasePage


class DashboardPage(BasePage):
    STAFF_LOGIN_USERNAME = "form input[name='username']"
    STAFF_LOGIN_PASSWORD = "form input[name='password']"
    STAFF_LOGIN_SUBMIT = "form button[type='submit'], form button"
    DASHBOARD_TITLE = "h1:has-text('Dashboard')"
    PRODUCTS_NAV_LINK = "a[href*='staff/products']"
    CATEGORIES_NAV_LINK = "a[href*='staff/categories']"
    ORDERS_NAV_LINK = "a[href*='staff/orders']"
    ANALYTICS_NAV_LINK = "a[href*='staff/analytics']"
    VERIFY_PAYMENT_BTN = "form[action*='verify-payment'] button"

    def open_staff_login(self):
        return self.navigate("/staff/login/")

    def open_dashboard_home(self):
        return self.navigate("/staff/")

    def open_product_management(self):
        return self.navigate("/staff/products/")

    def open_category_management(self):
        return self.navigate("/staff/categories/")

    def open_order_management(self):
        return self.navigate("/staff/orders/")

    def staff_login(self, username: str, password: str):
        self.open_staff_login()
        self.fill(self.STAFF_LOGIN_USERNAME, username)
        self.fill(self.STAFF_LOGIN_PASSWORD, password)
        self.click(self.STAFF_LOGIN_SUBMIT)
        self.page.wait_for_load_state("networkidle")
