"""
Temporary Production Super Admin Bootstrap Command

Creates a initial Super Admin user during Render deployment if
DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, and DJANGO_SUPERUSER_PASSWORD
environment variables are configured.

Safety & Idempotency:
- If the user does not exist, creates the account with hashed password and admin flags.
- If the matching user already exists, updates admin/active flags WITHOUT changing the existing password.
- If environment variables are missing, skips cleanly without failing build/deployment.
- Safe to be removed after the first successful production login.
"""

from decouple import config
from django.core.management.base import BaseCommand
from django.db.models import Q
from accounts.models import User


class Command(BaseCommand):
    help = "Creates or updates production Super Admin user idempotently from environment variables."

    def handle(self, *args, **options):
        username = (config("DJANGO_SUPERUSER_USERNAME", default="") or "").strip()
        email = (config("DJANGO_SUPERUSER_EMAIL", default="") or "").strip()
        password = (config("DJANGO_SUPERUSER_PASSWORD", default="") or "").strip()

        if not (username and email and password):
            self.stdout.write(
                self.style.WARNING(
                    "Production superadmin environment variables (DJANGO_SUPERUSER_USERNAME, "
                    "DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD) are not fully set. "
                    "Skipping production superadmin bootstrap."
                )
            )
            return

        user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=email)).first()

        if user:
            # Update admin permissions & active flags without changing existing password
            updated_fields = []
            if not user.is_staff:
                user.is_staff = True
                updated_fields.append("is_staff")
            if not user.is_superuser:
                user.is_superuser = True
                updated_fields.append("is_superuser")
            if not user.is_active:
                user.is_active = True
                updated_fields.append("is_active")
            if not getattr(user, "is_email_verified", False):
                user.is_email_verified = True
                updated_fields.append("is_email_verified")

            if updated_fields:
                user.save(update_fields=updated_fields)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Existing user '{user.username}' found. Updated permissions: {', '.join(updated_fields)}."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Existing superadmin user '{user.username}' is already configured with full admin permissions."
                    )
                )
        else:
            # Create new Super Admin user
            user = User(
                username=username,
                email=email,
                is_staff=True,
                is_superuser=True,
                is_active=True,
                is_email_verified=True,
            )
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Production superadmin user '{username}' successfully created with full admin privileges."
                )
            )
