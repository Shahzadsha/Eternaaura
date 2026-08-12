"""
Tests for production superadmin bootstrap command.
"""

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from accounts.models import User


class ProductionSuperadminBootstrapTest(TestCase):
    def setUp(self):
        self.out = StringIO()

    @patch("accounts.management.commands.create_production_superadmin.config")
    def test_creates_superadmin_when_env_vars_provided(self, mock_config):
        """Test creating a new superadmin user when all 3 env vars are set."""
        mock_config.side_effect = lambda key, default="": {
            "DJANGO_SUPERUSER_USERNAME": "superadmin_test",
            "DJANGO_SUPERUSER_EMAIL": "superadmin_test@example.com",
            "DJANGO_SUPERUSER_PASSWORD": "SecretSuperPassword123!",
        }.get(key, default)

        call_command("create_production_superadmin", stdout=self.out)

        user = User.objects.filter(username="superadmin_test").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "superadmin_test@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.check_password("SecretSuperPassword123!"))
        self.assertIn("successfully created", self.out.getvalue())

    @patch("accounts.management.commands.create_production_superadmin.config")
    def test_idempotent_without_overwriting_existing_password(self, mock_config):
        """Test that running the command on an existing user updates admin flags without resetting password."""
        existing_user = User.objects.create_user(
            username="existing_admin",
            email="existing_admin@example.com",
            password="OriginalPassword987!",
            is_staff=False,
            is_superuser=False,
            is_active=True,
            is_email_verified=False,
        )

        mock_config.side_effect = lambda key, default="": {
            "DJANGO_SUPERUSER_USERNAME": "existing_admin",
            "DJANGO_SUPERUSER_EMAIL": "existing_admin@example.com",
            "DJANGO_SUPERUSER_PASSWORD": "NewDifferentPassword456!",
        }.get(key, default)

        call_command("create_production_superadmin", stdout=self.out)

        existing_user.refresh_from_db()
        self.assertTrue(existing_user.is_staff)
        self.assertTrue(existing_user.is_superuser)
        self.assertTrue(existing_user.is_email_verified)
        # Password must remain OriginalPassword987!, NOT NewDifferentPassword456!
        self.assertTrue(existing_user.check_password("OriginalPassword987!"))
        self.assertFalse(existing_user.check_password("NewDifferentPassword456!"))
        self.assertIn("Existing user 'existing_admin' found", self.out.getvalue())

    @patch("accounts.management.commands.create_production_superadmin.config")
    def test_skips_when_env_vars_missing(self, mock_config):
        """Test cleanly skipping bootstrap when env vars are missing or empty."""
        mock_config.side_effect = lambda key, default="": ""

        call_command("create_production_superadmin", stdout=self.out)

        self.assertEqual(User.objects.filter(is_superuser=True).count(), 0)
        self.assertIn("Skipping production superadmin bootstrap", self.out.getvalue())
