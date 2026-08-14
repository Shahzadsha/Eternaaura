from urllib.parse import urlparse
import cloudinary
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Safely inspects Cloudinary SDK and storage configuration without exposing API secrets."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== ETERNAAURA Cloudinary Configuration Diagnostic ==="))

        c_url = getattr(settings, "CLOUDINARY_URL", None)
        c_storage = getattr(settings, "CLOUDINARY_STORAGE", {})
        config = cloudinary.config()

        cloud_name = config.cloud_name or c_storage.get("CLOUD_NAME")
        api_key = config.api_key or c_storage.get("API_KEY")
        api_secret = config.api_secret or c_storage.get("API_SECRET")

        if not cloud_name and c_url:
            try:
                parsed = urlparse(c_url)
                cloud_name = parsed.hostname
                api_key = api_key or parsed.username
                api_secret = api_secret or parsed.password
            except Exception:
                pass

        api_key_masked = (
            f"{api_key[:4]}...{api_key[-4:]}"
            if api_key and len(api_key) >= 8
            else ("Configured" if api_key else "Missing")
        )

        storage_backend = settings.STORAGES.get("default", {}).get("BACKEND", "Unknown")

        try:
            import importlib.metadata
            c_sdk_ver = importlib.metadata.version("cloudinary")
            c_storage_ver = importlib.metadata.version("django-cloudinary-storage")
        except Exception:
            c_sdk_ver = getattr(cloudinary, "VERSION", "Unknown")
            c_storage_ver = "Unknown"

        self.stdout.write(f"  - CLOUDINARY_URL configured: {bool(c_url)}")
        self.stdout.write(f"  - Cloud Name: {cloud_name or 'Not set'}")
        self.stdout.write(f"  - API Key identifier: {api_key_masked}")
        self.stdout.write(f"  - API Secret present: {bool(api_secret)}")
        self.stdout.write(f"  - Storage backend: {storage_backend}")
        self.stdout.write(f"  - Cloudinary Python SDK version: {c_sdk_ver}")
        self.stdout.write(f"  - django-cloudinary-storage version: {c_storage_ver}")

        if c_url and cloud_name and api_key and api_secret:
            self.stdout.write(self.style.SUCCESS("✓ Cloudinary configuration loaded successfully and synchronized across Django & SDK."))
        else:
            self.stdout.write(self.style.WARNING("! Local development mode: CLOUDINARY_URL is not set. Files fall back to FileSystemStorage."))
