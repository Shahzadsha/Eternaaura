from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import User


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ["username", "email", "phone_number", "password1", "password2"]


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
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email address is already in use by another account.")
        return email

