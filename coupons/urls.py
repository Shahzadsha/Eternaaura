from django.urls import path
from . import views

app_name = "coupons"

urlpatterns = [
    path("", views.CouponListView.as_view(), name="list"),
    path("apply/", views.ApplyCouponView.as_view(), name="apply"),
    path("remove/", views.RemoveCouponView.as_view(), name="remove"),
]

