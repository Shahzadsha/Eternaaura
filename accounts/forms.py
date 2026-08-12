from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import User


try:
    from disposable_email_domains import blocklist as _PYPI_BLOCKLIST
    DISPOSABLE_DOMAINS = set(_PYPI_BLOCKLIST)
except ImportError:
    DISPOSABLE_DOMAINS = set()

EXTRA_DISPOSABLE_DOMAINS = {
    "tempmail.com", "tempmail.net", "temp-mail.org", "10minutemail.com",
    "mailinator.com", "guerrillamail.com", "yopmail.com", "throwawaymail.com",
    "trashmail.com", "getnada.com", "dispostable.com", "sharklasers.com",
    "fakemailgenerator.com", "maildrop.cc", "crazymailing.com", "mohmal.com",
    "tmail.ws", "generator.email", "inboxkitten.com",
}
DISPOSABLE_DOMAINS.update(EXTRA_DISPOSABLE_DOMAINS)


def is_disposable_email(email):
    """
    Returns True if the email domain matches a known disposable email domain.
    """
    if not email or "@" not in email:
        return False
    domain = email.split("@")[-1].strip().lower()
    return domain in DISPOSABLE_DOMAINS


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        error_messages={"invalid": "Enter a valid email address."}
    )
    phone_number = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ["username", "email", "phone_number", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise ValidationError("Email address is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        if is_disposable_email(email):
            raise ValidationError("Please use a permanent email address.")
        return email


class EternaAuraAuthenticationForm(AuthenticationForm):
    """Blocks sign-in for customers who haven't completed email/OTP verification yet.
    Staff/superuser accounts are exempt so the private dashboard login never gets
    locked out by this customer-facing check."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not (user.is_staff or user.is_superuser) and not user.is_email_verified:
            raise ValidationError(
                "Please verify your email with the OTP we sent before signing in.",
                code="unverified",
            )


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    gender = forms.ChoiceField(choices=User.Gender.choices, required=False)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "date_of_birth", "gender", "avatar"]

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email address is already in use by another account.")
        if is_disposable_email(email):
            raise ValidationError("Please use a permanent email address.")
        return email

