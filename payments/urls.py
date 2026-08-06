from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("status/<uuid:order_id>/", views.PaymentStatusView.as_view(), name="status"),
    path("qr/<uuid:payment_id>/", views.UPIQRCodeView.as_view(), name="upi_qr"),
    path("qr-preview/", views.UPIPreviewQRCodeView.as_view(), name="upi_qr_preview"),
]
