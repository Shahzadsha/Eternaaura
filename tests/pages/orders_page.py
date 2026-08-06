"""
Page Object Model for Customer Order History & Order Details.
"""
from tests.pages.base_page import BasePage


class OrdersPage(BasePage):
    ORDER_HISTORY_TITLE = "h1:has-text('Order History'), h1:has-text('My Orders')"
    ORDER_ROW = ".order-card, tbody tr"
    ORDER_DETAIL_TITLE = "h1:has-text('Order #')"
    ORDER_STATUS_BADGE = "[data-order-status]"

    def open_history(self):
        return self.navigate("/orders/history/")

    def open_order_detail(self, order_id: str):
        return self.navigate(f"/orders/{order_id}/")

    def open_order_track(self, order_id: str):
        return self.navigate(f"/orders/{order_id}/track/")
