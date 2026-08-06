"""
Page Object Model for EternaAura User Registration, Login, Profile & Address Management.
"""
from tests.pages.base_page import BasePage


class AccountsPage(BasePage):
    # Registration Locators
    REG_USERNAME = "main form #id_username"
    REG_EMAIL = "main form #id_email"
    REG_PASSWORD1 = "main form #id_password1"
    REG_PASSWORD2 = "main form #id_password2"
    REG_SUBMIT = "main form button:has-text('Register')"

    # Login Locators
    LOGIN_USERNAME = "main form #id_username"
    LOGIN_PASSWORD = "main form #id_password"
    LOGIN_SUBMIT = "main form button:has-text('Sign In')"

    # OTP Locators
    OTP_INPUT = "main form input[name='code']"
    OTP_SUBMIT = "main form button:has-text('Verify')"
    RESEND_OTP_LINK = "main a[href*='resend-otp']"

    # Password Reset Locators
    RESET_EMAIL_INPUT = "main form input[name='email']"
    RESET_SUBMIT = "main form button:has-text('Send Reset Link')"

    def open_login(self):
        return self.navigate("/account/login/")

    def open_register(self):
        return self.navigate("/account/register/")

    def open_password_reset(self):
        return self.navigate("/account/password-reset/")

    def open_profile(self):
        return self.navigate("/account/profile/")

    def open_addresses(self):
        return self.navigate("/account/addresses/")

    def login(self, username: str, password: str):
        self.open_login()
        self.fill(self.LOGIN_USERNAME, username)
        self.fill(self.LOGIN_PASSWORD, password)
        self.click(self.LOGIN_SUBMIT)
        self.page.wait_for_load_state("networkidle")

    def register(self, username: str, email: str, password: str):
        self.open_register()
        self.fill(self.REG_USERNAME, username)
        self.fill(self.REG_EMAIL, email)
        self.fill(self.REG_PASSWORD1, password)
        self.fill(self.REG_PASSWORD2, password)
        self.click(self.REG_SUBMIT)
        self.page.wait_for_load_state("networkidle")

    def verify_otp(self, code: str):
        self.fill(self.OTP_INPUT, code)
        self.click(self.OTP_SUBMIT)
        self.page.wait_for_load_state("networkidle")
