from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class DashboardSecurityTests(TestCase):
    def setUp(self):
        self.regular_user = User.objects.create_user(
            username="regular@eternaaura.com",
            email="regular@eternaaura.com",
            first_name="Regular",
            last_name="User",
            password="SecurePassword123!",
            is_active=True,
            is_staff=False,
        )
        self.staff_user = User.objects.create_user(
            username="staff@eternaaura.com",
            email="staff@eternaaura.com",
            first_name="Staff",
            last_name="Admin",
            password="SecurePassword123!",
            is_active=True,
            is_staff=True,
        )


    def test_staff_area_protection_middleware(self):
        dashboard_url = reverse("dashboard:home")

        # 1. Unauthenticated user -> redirected to dashboard login
        res1 = self.client.get(dashboard_url)
        self.assertEqual(res1.status_code, 302)

        # 2. Regular non-staff user -> redirected to dashboard login
        self.client.login(username="regular@eternaaura.com", password="SecurePassword123!")
        res2 = self.client.get(dashboard_url)
        self.assertEqual(res2.status_code, 302)

        # 3. Staff user -> access granted
        self.client.login(username="staff@eternaaura.com", password="SecurePassword123!")
        res3 = self.client.get(dashboard_url)
        self.assertEqual(res3.status_code, 200)

