"""
Automated Web Crawler & Asset Auditor for Playwright test suite.
"""
from urllib.parse import urlparse
from playwright.sync_api import Page


class SiteCrawler:
    """
    Crawls internal application pages starting from home page,
    validates HTTP response status codes, checks image loading,
    and captures browser console errors.
    """
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")
        self.visited = set()
        self.broken_links = []
        self.broken_images = []
        self.console_errors = []

        # Listen for console errors
        self.page.on("console", self._handle_console)

    def _handle_console(self, msg):
        if msg.type == "error":
            self.console_errors.append(f"[{self.page.url}] {msg.text}")

    def crawl_url(self, relative_path: str = "/") -> dict:
        target_url = f"{self.base_url}/{relative_path.lstrip('/')}"
        if target_url in self.visited:
            return {"status": 200, "url": target_url, "visited": True}

        self.visited.add(target_url)

        try:
            response = self.page.goto(target_url, wait_until="networkidle", timeout=10000)
            status = response.status if response else 500
        except Exception as e:
            status = 500
            self.broken_links.append({"url": target_url, "status": 500, "error": str(e)})
            return {"status": 500, "url": target_url, "error": str(e)}

        if status >= 400:
            self.broken_links.append({"url": target_url, "status": status})

        # Audit rendered images on page
        unrendered = self.page.evaluate("""
            () => Array.from(document.querySelectorAll('img'))
                       .filter(img => img.src && (!img.complete || img.naturalWidth === 0))
                       .map(img => img.src)
        """)
        for img_src in unrendered:
            self.broken_images.append({"page": target_url, "image_src": img_src})

        return {"status": status, "url": target_url, "broken_images_count": len(unrendered)}
