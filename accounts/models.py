import secrets
import string
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from config.validators import validate_image_extension, validate_image_size


class User(AbstractUser):
    """Custom user so we can attach phone/OTP-verification fields cleanly."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    date_of_birth = models.DateField(null=True, blank=True)
    class Gender(models.TextChoices):
        UNSPECIFIED = "unspecified", "Prefer not to say"
        FEMALE = "female", "Female"
        MALE = "male", "Male"
        OTHER = "other", "Other"

    gender = models.CharField(max_length=15, choices=Gender.choices, default=Gender.UNSPECIFIED)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True, validators=[validate_image_extension, validate_image_size])
    created_at = models.DateTimeField(auto_now_add=True)



    # Staff role granularity used by the dashboard RBAC system (Phase 5)
    class StaffRole(models.TextChoices):
        NONE = "none", "Not staff"
        SUPER_ADMIN = "super_admin", "Super Admin"
        PRODUCT_MANAGER = "product_manager", "Product Manager"
        ORDER_MANAGER = "order_manager", "Order Manager"
        CUSTOMER_SUPPORT = "customer_support", "Customer Support"
        CONTENT_MANAGER = "content_manager", "Content Manager"
        MARKETING_MANAGER = "marketing_manager", "Marketing Manager"

    staff_role = models.CharField(max_length=20, choices=StaffRole.choices, default=StaffRole.NONE)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return self.get_full_name() or self.username


class Address(models.Model):
    class AddressType(models.TextChoices):
        HOME = "home", "Home"
        WORK = "work", "Work"
        OTHER = "other", "Other"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    address_type = models.CharField(max_length=10, choices=AddressType.choices, default=AddressType.HOME)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="India")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.full_name} — {self.city}, {self.state}"

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class OTPVerification(models.Model):
    """One-time-password used for email/phone verification and password reset."""

    class Purpose(models.TextChoices):
        REGISTRATION = "registration", "Registration"
        LOGIN = "login", "Login"
        PASSWORD_RESET = "password_reset", "Password reset"
        PHONE_VERIFY = "phone_verify", "Phone verification"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @staticmethod
    def generate_code():
        return "".join(secrets.choice(string.digits) for _ in range(6))

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    def __str__(self):
        return f"OTP({self.user}, {self.purpose})"
