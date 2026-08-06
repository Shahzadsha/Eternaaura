from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("login/", views.StaffLoginView.as_view(), name="login"),
    path("", views.DashboardHomeView.as_view(), name="home"),

    path("products/", views.ProductManagementView.as_view(), name="products"),
    path("products/new/", views.ProductCreateView.as_view(), name="product_create"),
    path("products/<uuid:pk>/edit/", views.ProductUpdateView.as_view(), name="product_edit"),
    path("products/<uuid:pk>/delete/", views.ProductDeleteView.as_view(), name="product_delete"),
    path("products/<uuid:pk>/toggle-publish/", views.ProductTogglePublishView.as_view(), name="product_toggle_publish"),
    path("products/<uuid:pk>/images/<int:image_id>/delete/", views.ProductImageDeleteView.as_view(), name="product_image_delete"),

    path("categories/", views.CategoryManagementView.as_view(), name="categories"),
    path("categories/new/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_edit"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),

    path("banners/", views.BannerManagementView.as_view(), name="banners"),
    path("banners/new/", views.BannerCreateView.as_view(), name="banner_create"),
    path("banners/<int:pk>/edit/", views.BannerUpdateView.as_view(), name="banner_edit"),
    path("banners/<int:pk>/delete/", views.BannerDeleteView.as_view(), name="banner_delete"),

    path("orders/", views.OrderManagementView.as_view(), name="orders"),
    path("orders/<uuid:pk>/verify-payment/", views.VerifyPaymentView.as_view(), name="order_verify_payment"),
    path("analytics/", views.AnalyticsView.as_view(), name="analytics"),
    path("api/revenue-analytics/", views.DailyRevenueApiView.as_view(), name="revenue_analytics_api"),
]
