from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import Address, OTPVerification

User = get_user_model()


class AccountsFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser@eternaaura.com",
            email="testuser@eternaaura.com",
            first_name="Eterna",
            last_name="Customer",
            password="SecurePassword123!",
            is_active=True,
            is_email_verified=True,
        )


    def test_user_login_and_logout(self):
        # Test Login
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "testuser@eternaaura.com", "password": "SecurePassword123!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue("_auth_user_id" in self.client.session)

        # Test Logout View
        logout_response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(logout_response.status_code, 302)
        self.assertFalse("_auth_user_id" in self.client.session)

    def test_protected_profile_view_cache_headers(self):
        # Unauthenticated access redirects
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)

        # Authenticated access gets no-cache headers
        self.client.login(username="testuser@eternaaura.com", password="SecurePassword123!")
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-cache", response.headers.get("Cache-Control", ""))

    def test_address_creation(self):
        self.client.login(username="testuser@eternaaura.com", password="SecurePassword123!")
        response = self.client.post(
            reverse("accounts:address_add"),
            {
                "full_name": "Test Customer",
                "phone_number": "+919876543210",
                "address_type": "home",
                "line1": "Flat 101, Eterna Towers",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400001",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Address.objects.filter(user=self.user).count(), 1)

    def test_edit_profile_flow(self):
        self.client.login(username="testuser@eternaaura.com", password="SecurePassword123!")
        edit_url = reverse("accounts:profile_edit")
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        # Post profile updates
        post_res = self.client.post(
            edit_url,
            {
                "action": "update_profile",
                "first_name": "Aura",
                "last_name": "Eterna",
                "email": "testuser@eternaaura.com",
                "phone_number": "+919999988888",
                "gender": "female",
            },
        )
        self.assertEqual(post_res.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Aura")
        self.assertEqual(self.user.last_name, "Eterna")
        self.assertEqual(self.user.phone_number, "+919999988888")
        self.assertEqual(self.user.gender, "female")


