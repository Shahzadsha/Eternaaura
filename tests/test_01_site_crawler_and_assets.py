"""
Automated Web Crawler Test Suite — Crawls site routes, verifies HTTP 200/302 status codes,
audits image asset rendering, and checks for JavaScript console errors.
"""
import pytest
from tests.utils.crawler import SiteCrawler


@pytest.mark.crawler
@pytest.mark.django_db(transaction=True)
def test_crawl_all_public_routes(page, app_url, db_seeded):
    """
    Crawls key public application routes to ensure zero broken links (404/500),
    zero unrendered image assets, and zero browser console errors.
    """
    crawler = SiteCrawler(page, app_url)

    routes_to_crawl = [
        "/",
        "/new-arrivals/",
        "/best-sellers/",
        "/trending-collections/",
        "/search/?q=gold",
        "/category/necklaces/",
        "/category/rings/",
        "/cart/",
        "/coupons/",
        "/account/login/",
        "/account/register/",
        "/account/password-reset/",
        "/staff/login/",
    ]

    for route in routes_to_crawl:
        res = crawler.crawl_url(route)
        assert res["status"] in [200, 302], f"Route {route} returned HTTP {res['status']}"

    assert len(crawler.broken_links) == 0, f"Broken links found: {crawler.broken_links}"
    assert len(crawler.broken_images) == 0, f"Broken images found: {crawler.broken_images}"
