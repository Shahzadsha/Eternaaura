from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("status/<uuid:order_id>/", views.PaymentStatusView.as_view(), name="status"),
]
