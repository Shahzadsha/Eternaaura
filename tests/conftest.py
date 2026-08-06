"""
Pytest configuration, Playwright browser fixtures, Django live server integration,
authentication helpers, and test failure hooks (screenshots, logs, traces).
"""
import os
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright

from tests.fixtures.db_fixtures import seed_test_database
from tests.data.test_data import TEST_USERS

BASE_DIR = Path(__file__).resolve().parent.parent

# Create required output folders
for folder in ["screenshots", "reports", "logs", "videos", "traces"]:
    (BASE_DIR / "tests" / folder).mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session", autouse=True)
def setup_test_directories():
    """Ensures output directories exist prior to test runs."""
    for folder in ["screenshots", "reports", "logs", "videos", "traces"]:
        (BASE_DIR / "tests" / folder).mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="function")
def db_seeded(db):
    """Populates Django ORM test database for each test function."""
    return seed_test_database()


@pytest.fixture(scope="function")
def app_url(live_server):
    """Provides base URL for live Django server."""
    return live_server.url


@pytest.fixture(scope="function")
def console_logs():
    """Collects browser console error messages during test execution."""
    logs = []
    return logs


@pytest.fixture(scope="function")
def network_errors():
    """Collects HTTP 400/500 network errors during test execution."""
    errors = []
    return errors


@pytest.fixture(scope="function")
def page_with_logging(page, console_logs, network_errors):
    """
    Attaches console and network response listeners to Playwright page object.
    """
    def handle_console(msg):
        if msg.type in ["error", "warning"]:
            console_logs.append(f"[{msg.type.upper()}] {msg.text}")

    def handle_response(response):
        if response.status >= 400:
            network_errors.append(f"[{response.status}] {response.url}")

    page.on("console", handle_console)
    page.on("response", handle_response)
    return page


@pytest.fixture(scope="function")
def customer_page(context, app_url, db_seeded):
    """
    Returns a Playwright Page instance logged in as a registered customer.
    """
    page = context.new_page()
    page.goto(f"{app_url}/account/login/")
    page.fill("main form #id_username", TEST_USERS["customer"]["username"])
    page.fill("main form #id_password", TEST_USERS["customer"]["password"])
    page.click("main form button:has-text('Sign In')")
    page.wait_for_load_state("networkidle")
    return page


@pytest.fixture(scope="function")
def staff_page(context, app_url, db_seeded):
    """
    Returns a Playwright Page instance logged in as a staff manager.
    """
    page = context.new_page()
    page.goto(f"{app_url}/staff/login/")
    page.fill("form input[name='username']", TEST_USERS["staff"]["username"])
    page.fill("form input[name='password']", TEST_USERS["staff"]["password"])
    page.click("form button")
    page.wait_for_load_state("networkidle")
    return page


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Failure Hook: Captures screenshot, browser console logs, and Playwright trace on test failure.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        test_name = item.name.replace("[", "_").replace("]", "_")

        # Capture Playwright page screenshot if page fixture present
        page = item.funcargs.get("page") or item.funcargs.get("customer_page") or item.funcargs.get("staff_page")
        if page:
            screenshot_path = BASE_DIR / "tests" / "screenshots" / f"FAILED_{test_name}.png"
            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
            except Exception:
                pass

        # Write console/network log output
        logs = item.funcargs.get("console_logs", [])
        net_errors = item.funcargs.get("network_errors", [])
        if logs or net_errors:
            log_file = BASE_DIR / "tests" / "logs" / f"FAILED_{test_name}.log"
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("=== CONSOLE LOGS ===\n")
                f.write("\n".join(logs) + "\n\n")
                f.write("=== NETWORK ERRORS ===\n")
                f.write("\n".join(net_errors) + "\n")
