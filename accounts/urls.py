from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("verify-otp/", views.VerifyOTPView.as_view(), name="verify_otp"),
    path("resend-otp/", views.ResendOTPView.as_view(), name="resend_otp"),
    path("password-reset/", views.PasswordResetRequestView.as_view(), name="password_reset"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.EditProfileView.as_view(), name="profile_edit"),
    path("addresses/", views.AddressListView.as_view(), name="addresses"),

    path("addresses/add/", views.AddressCreateView.as_view(), name="address_add"),
    path("addresses/<int:pk>/delete/", views.AddressDeleteView.as_view(), name="address_delete"),
    path("wishlist/", views.WishlistView.as_view(), name="wishlist"),
]
