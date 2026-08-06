"""
Base Page Object Model with shared navigation, interaction, element verification,
and asset inspection utilities using clean Playwright locators.
"""
import re
from playwright.sync_api import Page, expect


class BasePage:
    def __init__(self, page: Page, base_url: str = ""):
        self.page = page
        self.base_url = base_url

    def navigate(self, relative_url: str = ""):
        target = f"{self.base_url.rstrip('/')}/{relative_url.lstrip('/')}" if self.base_url else relative_url
        response = self.page.goto(target)
        self.page.wait_for_load_state("networkidle")
        return response

    def click(self, selector: str, timeout: int = 5000):
        self.page.wait_for_selector(selector, timeout=timeout, state="visible")
        self.page.locator(selector).click()

    def fill(self, selector: str, value: str):
        self.page.wait_for_selector(selector, timeout=5000, state="visible")
        self.page.locator(selector).fill(value)

    def get_text(self, selector: str) -> str:
        return self.page.locator(selector).inner_text().strip()

    def is_visible(self, selector: str, timeout: int = 3000) -> bool:
        try:
            self.page.wait_for_selector(selector, timeout=timeout, state="visible")
            return True
        except Exception:
            return False

    def assert_title_contains(self, substring: str):
        pattern = re.compile(re.escape(substring), re.IGNORECASE)
        expect(self.page).to_have_title(pattern)

    def check_broken_images(self) -> list:
        """
        Executes JavaScript in the browser to check all image elements for non-zero natural dimensions.
        Returns a list of image src URLs that failed to render.
        """
        broken = self.page.evaluate("""
            () => {
                const images = Array.from(document.querySelectorAll('img'));
                return images
                    .filter(img => img.src && (!img.complete || img.naturalWidth === 0))
                    .map(img => img.src);
            }
        """)
        return broken
