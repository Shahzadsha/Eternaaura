from django.test import TestCase
from django.urls import reverse


class CouponPageTests(TestCase):
    def test_coupons_placeholder_page(self):
        url = reverse("coupons:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Coupon Codes")
        self.assertContains(response, "Available offers and discount codes will appear here soon.")
        self.assertContains(response, "No coupons available at the moment.")

