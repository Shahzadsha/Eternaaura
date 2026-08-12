from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("buy-now/<uuid:product_id>/", views.BuyNowView.as_view(), name="buy_now"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("history/", views.OrderHistoryView.as_view(), name="history"),
    path("<uuid:pk>/", views.OrderDetailView.as_view(), name="detail"),
    path("item/<int:item_id>/return/", views.RequestReturnView.as_view(), name="request_return"),
]

