from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.CartDetailView.as_view(), name="detail"),
    path("add/<uuid:product_id>/", views.AddToCartView.as_view(), name="add"),
    path("update/<int:item_id>/", views.UpdateCartItemView.as_view(), name="update"),
    path("remove/<int:item_id>/", views.RemoveCartItemView.as_view(), name="remove"),
]
