import time
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import ListView, TemplateView

from catalog.models import Wishlist
from .forms import EternaAuraAuthenticationForm, RegistrationForm, UserProfileForm
from .models import Address, OTPVerification, User


MAX_OTP_ATTEMPTS = 5


def send_otp_verification_email(user, code):
    """
    Renders and sends the luxury EternaAura OTP verification code email.
    """
    context = {
        "user": user,
        "user_display_name": user.first_name or user.username,
        "code": code,
    }
    text_content = render_to_string("accounts/emails/verification_code_email.txt", context)
    html_content = render_to_string("accounts/emails/verification_code_email.html", context)

    send_mail(
        subject="Your EternaAura verification code",
        message=text_content,
        html_message=html_content,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@eternaaura.com"),
        recipient_list=[user.email],
        fail_silently=False,
    )


class RegisterView(View):
    template_name = "accounts/register.html"

    def get(self, request):
        return render(request, self.template_name, {"form": RegistrationForm()})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            code = OTPVerification.generate_code()
            OTPVerification.objects.create(
                user=user,
                code=code,
                purpose=OTPVerification.Purpose.REGISTRATION,
                expires_at=timezone.now() + timezone.timedelta(minutes=10),
            )
            send_otp_verification_email(user, code)
            request.session["pending_verification_user_id"] = str(user.id)
            request.session["otp_attempts"] = 0
            messages.success(request, "Account created. Check your email for the OTP to verify your account.")
            return redirect("accounts:verify_otp")
        return render(request, self.template_name, {"form": form})


class NeverCacheLoginRequiredMixin(LoginRequiredMixin):

    """
    Combines LoginRequiredMixin with HTTP Cache-Control headers to prevent
    browsers from caching sensitive authenticated views (e.g. profile, addresses, orders).
    When a user logs out, hitting the browser Back button forces a fresh server request
    and redirects back to the login page safely.
    """

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        response = super().dispatch(*args, **kwargs)
        response["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response


def merge_guest_cart(request, user):
    """
    Merges unauthenticated guest session cart items into authenticated user cart upon login.
    """
    from cart.models import Cart, CartItem
    session_key = request.session.session_key
    if session_key:
        guest_cart = Cart.objects.filter(session_key=session_key, user=None).first()
        if guest_cart:
            user_cart, _ = Cart.objects.get_or_create(user=user)
            for guest_item in guest_cart.items.all():
                user_item, created = CartItem.objects.get_or_create(
                    cart=user_cart, product=guest_item.product, variant=guest_item.variant
                )
                if not created:
                    user_item.quantity += guest_item.quantity
                    if guest_item.product.stock_quantity:
                        user_item.quantity = min(user_item.quantity, guest_item.product.stock_quantity)
                else:
                    user_item.quantity = guest_item.quantity
                user_item.save()
            guest_cart.delete()


class LoginView(DjangoLoginView):
    template_name = "accounts/login.html"
    authentication_form = EternaAuraAuthenticationForm

    def post(self, request, *args, **kwargs):
        ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
        cache_key = f"login_attempts_{ip}"
        attempts = cache.get(cache_key, 0)

        if attempts >= 5:
            messages.error(request, "Too many failed login attempts. Please wait 5 minutes before trying again.")
            form = self.get_form()
            return self.form_invalid(form)

        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        ip = self.request.META.get("REMOTE_ADDR", "127.0.0.1")
        cache_key = f"login_attempts_{ip}"
        attempts = cache.get(cache_key, 0)
        cache.set(cache_key, attempts + 1, 300)
        return super().form_invalid(form)

    def form_valid(self, form):
        ip = self.request.META.get("REMOTE_ADDR", "127.0.0.1")
        cache_key = f"login_attempts_{ip}"
        cache.delete(cache_key)
        response = super().form_valid(form)
        merge_guest_cart(self.request, self.request.user)
        return response



class LogoutView(View):
    """
    Secure Logout Handler:
    - Flushes backend session storage completely.
    - Clears user auth cookies.
    - Adds user feedback message.
    - Enforces no-cache headers.
    - Redirects to login page.
    """

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        return self._do_logout(request)

    def get(self, request):
        return self._do_logout(request)

    def _do_logout(self, request):
        logout(request)
        request.session.flush()
        messages.success(request, "You have been successfully logged out of ETERNAAURA.")
        response = redirect("accounts:login")
        response.delete_cookie("sessionid")
        response["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response



class VerifyOTPView(View):
    template_name = "accounts/verify_otp.html"

    def get(self, request):
        if not request.session.get("pending_verification_user_id"):
            messages.info(request, "Please register first, or log in if you're already verified.")
            return redirect("accounts:register")
        return render(request, self.template_name)

    def post(self, request):
        pending_user_id = request.session.get("pending_verification_user_id")
        if not pending_user_id:
            messages.error(request, "Your verification session expired. Please register again.")
            return redirect("accounts:register")

        attempts = request.session.get("otp_attempts", 0)
        if attempts >= MAX_OTP_ATTEMPTS:
            del request.session["pending_verification_user_id"]
            messages.error(request, "Too many incorrect attempts. Please register again to receive a new code.")
            return redirect("accounts:register")

        code = request.POST.get("code", "")
        # Scoped to the user bound to THIS session — never a global code lookup —
        # so one person's OTP can't be used to verify or sign in as someone else.
        otp = OTPVerification.objects.filter(
            user_id=pending_user_id,
            code=code,
            purpose=OTPVerification.Purpose.REGISTRATION,
            is_used=False,
        ).order_by("-created_at").first()

        if otp and otp.is_valid():
            otp.is_used = True
            otp.save()
            otp.user.is_email_verified = True
            otp.user.save()
            del request.session["pending_verification_user_id"]
            request.session.pop("otp_attempts", None)
            login(request, otp.user)
            messages.success(request, "Account verified successfully.")
            return redirect("catalog:home")

        request.session["otp_attempts"] = attempts + 1
        messages.error(request, "Invalid or expired OTP.")
        return render(request, self.template_name)


class ResendOTPView(View):
    def get(self, request):
        pending_user_id = request.session.get("pending_verification_user_id")
        if not pending_user_id:
            messages.error(request, "Please register first.")
            return redirect("accounts:register")

        last_resend = request.session.get("last_otp_resend_time", 0)
        now = time.time()
        cooldown = 60
        if now - last_resend < cooldown:
            remaining = int(cooldown - (now - last_resend))
            messages.error(request, f"Please wait {remaining} seconds before requesting a new code.")
            return redirect("accounts:verify_otp")

        user = get_object_or_404(User, pk=pending_user_id)
        request.session["last_otp_resend_time"] = now
        code = OTPVerification.generate_code()
        OTPVerification.objects.create(
            user=user,
            code=code,
            purpose=OTPVerification.Purpose.REGISTRATION,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        send_otp_verification_email(user, code)
        request.session["otp_attempts"] = 0
        messages.success(request, "A new code has been sent.")
        return redirect("accounts:verify_otp")


class VerificationCodeEmailPreviewView(View):
    """
    Developer/Admin preview view for visual inspection of the luxury verification code email template.
    """

    def get(self, request):
        user_display_name = request.GET.get("name", "Asdfgh")
        code = request.GET.get("code", "206821")
        user_obj = getattr(request, "user", None)
        user = user_obj if (user_obj and user_obj.is_authenticated) else None
        context = {
            "user": user,
            "user_display_name": user_display_name,
            "code": code,
        }
        return render(request, "accounts/emails/verification_code_email.html", context)


class PasswordResetRequestView(View):
    template_name = "accounts/password_reset.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email", "").strip()
        if email:
            user = User.objects.filter(email__iexact=email, is_active=True).first()
            if user:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = request.build_absolute_uri(
                    reverse("accounts:password_reset_confirm", kwargs={"uidb64": uid, "token": token})
                )
                context = {
                    "user": user,
                    "user_display_name": user.first_name or user.username,
                    "reset_url": reset_url,
                }
                text_content = render_to_string("accounts/emails/password_reset_email.txt", context)
                html_content = render_to_string("accounts/emails/password_reset_email.html", context)

                send_mail(
                    subject="EternaAura — Password Reset Request",
                    message=text_content,
                    html_message=html_content,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@eternaaura.com"),
                    recipient_list=[user.email],
                    fail_silently=not settings.DEBUG,
                )
        messages.success(request, "If that email exists, a reset link has been sent.")
        return redirect("accounts:login")


class PasswordResetEmailPreviewView(View):
    """
    Developer/Admin preview view for visual inspection of the luxury password reset email template.
    """

    def get(self, request):
        sample_url = request.build_absolute_uri(
            reverse("accounts:password_reset_confirm", kwargs={"uidb64": "sample-uid", "token": "sample-token"})
        )
        user_display_name = request.GET.get("name", "Najiha")
        user_obj = getattr(request, "user", None)
        user = user_obj if (user_obj and user_obj.is_authenticated) else None
        context = {
            "user": user,
            "user_display_name": user_display_name,
            "reset_url": sample_url,
        }
        return render(request, "accounts/emails/password_reset_email.html", context)


class PasswordResetConfirmView(View):
    template_name = "accounts/password_reset_confirm.html"

    def _get_user(self, uidb64):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return User.objects.get(pk=uid, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    def get(self, request, uidb64, token):
        user = self._get_user(uidb64)
        validlink = bool(user and default_token_generator.check_token(user, token))
        return render(request, self.template_name, {"validlink": validlink})

    def post(self, request, uidb64, token):
        user = self._get_user(uidb64)
        if not user or not default_token_generator.check_token(user, token):
            messages.error(request, "Invalid or expired password reset link.")
            return render(request, self.template_name, {"validlink": False})

        password1 = request.POST.get("password1", "").strip()
        password2 = request.POST.get("password2", "").strip()

        if not password1 or len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, self.template_name, {"validlink": True})

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, self.template_name, {"validlink": True})

        user.set_password(password1)
        user.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Your password has been reset successfully. Please sign in with your new password.")
        return redirect("accounts:login")


class ProfileView(NeverCacheLoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"


class EditProfileView(NeverCacheLoginRequiredMixin, View):
    template_name = "accounts/profile_edit.html"

    def get(self, request):
        user_form = UserProfileForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)
        return render(request, self.template_name, {
            "user_form": user_form,
            "password_form": password_form,
        })

    def post(self, request):
        action = request.POST.get("action")
        user_form = UserProfileForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)

        if action == "update_profile":
            user_form = UserProfileForm(request.POST, request.FILES, instance=request.user)
            if user_form.is_valid():
                old_email = request.user.email
                user = user_form.save(commit=False)
                if user.email != old_email:
                    user.is_email_verified = False
                    messages.info(request, "Email address changed. Please verify your new email address.")
                user.save()
                user_form.save_m2m()
                messages.success(request, "Your profile information has been updated successfully.")
                return redirect("accounts:profile_edit")
            else:
                messages.error(request, "Please correct the errors in your profile information.")

        elif action == "change_password":
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been changed successfully.")
                return redirect("accounts:profile_edit")
            else:
                messages.error(request, "Please correct the errors in the password form.")

        return render(request, self.template_name, {
            "user_form": user_form,
            "password_form": password_form,
        })



class AddressListView(NeverCacheLoginRequiredMixin, ListView):
    template_name = "accounts/addresses.html"
    context_object_name = "addresses"

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class AddressCreateView(NeverCacheLoginRequiredMixin, View):
    template_name = "accounts/address_form.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        full_name = request.POST.get("full_name", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        address_type = request.POST.get("address_type", "home")
        line1 = request.POST.get("line1", "").strip()
        line2 = request.POST.get("line2", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        postal_code = request.POST.get("postal_code", "").strip()
        is_default = request.POST.get("is_default") == "on"

        if not all([full_name, phone_number, line1, city, state, postal_code]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, self.template_name)

        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone_number=phone_number,
            address_type=address_type,
            line1=line1,
            line2=line2,
            city=city,
            state=state,
            postal_code=postal_code,
            is_default=is_default or (request.user.addresses.count() == 0),
        )
        messages.success(request, "Address saved successfully.")
        return redirect("accounts:addresses")


class AddressDeleteView(NeverCacheLoginRequiredMixin, View):
    def post(self, request, pk):
        addr = get_object_or_404(Address, pk=pk, user=request.user)
        addr.delete()
        messages.success(request, "Address removed.")
        return redirect("accounts:addresses")


class WishlistView(NeverCacheLoginRequiredMixin, ListView):
    template_name = "accounts/wishlist.html"
    context_object_name = "wishlist_items"

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related("product", "product__category").prefetch_related("product__images")

