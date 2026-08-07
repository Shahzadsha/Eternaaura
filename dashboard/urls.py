from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("login/", views.StaffLoginView.as_view(), name="login"),
    path("logout/", views.StaffLogoutView.as_view(), name="logout"),
    path("", views.DashboardHomeView.as_view(), name="home"),

    # Products & Catalog
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

    path("collections/", views.CollectionManagementView.as_view(), name="collections"),
    path("collections/new/", views.CollectionCreateView.as_view(), name="collection_create"),
    path("collections/<int:pk>/edit/", views.CollectionUpdateView.as_view(), name="collection_edit"),
    path("collections/<int:pk>/delete/", views.CollectionDeleteView.as_view(), name="collection_delete"),

    path("inventory/", views.InventoryView.as_view(), name="inventory"),
    path("reviews/", views.ReviewModerationView.as_view(), name="reviews"),
    path("reviews/<int:pk>/toggle-approve/", views.ReviewToggleApproveView.as_view(), name="review_toggle_approve"),
    path("reviews/<int:pk>/delete/", views.ReviewDeleteView.as_view(), name="review_delete"),

    # Orders & Payments
    path("orders/", views.OrderManagementView.as_view(), name="orders"),
    path("orders/<uuid:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("orders/<uuid:pk>/update-status/", views.OrderStatusUpdateView.as_view(), name="order_update_status"),
    path("orders/<uuid:pk>/verify-payment/", views.VerifyPaymentView.as_view(), name="order_verify_payment"),
    path("payments/", views.PaymentListView.as_view(), name="payments"),
    path("refunds/", views.RefundListView.as_view(), name="refunds"),
    path("refunds/<int:pk>/approve/", views.ApproveRefundView.as_view(), name="refund_approve"),

    # Customers
    path("customers/", views.CustomerListView.as_view(), name="customers"),
    path("customers/<uuid:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("customers/<uuid:pk>/toggle-active/", views.CustomerToggleActiveView.as_view(), name="customer_toggle_active"),

    # Marketing
    path("banners/", views.BannerListView.as_view(), name="banners"),
    path("banners/new/", views.BannerCreateView.as_view(), name="banner_create"),
    path("banners/<int:pk>/edit/", views.BannerUpdateView.as_view(), name="banner_edit"),
    path("banners/<int:pk>/delete/", views.BannerDeleteView.as_view(), name="banner_delete"),

    path("coupons/", views.CouponListView.as_view(), name="coupons"),
    path("coupons/new/", views.CouponCreateView.as_view(), name="coupon_create"),
    path("coupons/<int:pk>/edit/", views.CouponUpdateView.as_view(), name="coupon_edit"),
    path("coupons/<int:pk>/delete/", views.CouponDeleteView.as_view(), name="coupon_delete"),

    path("newsletter/", views.NewsletterSubscriberListView.as_view(), name="newsletter"),

    # Analytics & Reports
    path("analytics/", views.AnalyticsView.as_view(), name="analytics"),
    path("api/revenue-analytics/", views.DailyRevenueApiView.as_view(), name="revenue_analytics_api"),
    path("reports/", views.ReportsOverviewView.as_view(), name="reports"),
    path("reports/export/orders/", views.ReportExportOrdersExcelView.as_view(), name="reports_export_orders"),
    path("reports/export/products/", views.ReportExportProductsExcelView.as_view(), name="reports_export_products"),
    path("reports/export/customers/", views.ReportExportCustomersExcelView.as_view(), name="reports_export_customers"),
    path("reports/pdf/sales/", views.ReportSalesPdfView.as_view(), name="reports_pdf_sales"),

    # Settings & Profile
    path("settings/", views.StoreSettingsView.as_view(), name="settings"),
    path("profile/", views.AdminProfileView.as_view(), name="profile"),
]

