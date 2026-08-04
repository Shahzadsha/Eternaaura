from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("new-arrivals/", views.NewArrivalsView.as_view(), name="new_arrivals"),
    path("best-sellers/", views.BestSellersView.as_view(), name="best_sellers"),
    path("trending-collections/", views.TrendingCollectionsView.as_view(), name="trending"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("category/<slug:slug>/", views.CategoryDetailView.as_view(), name="category_detail"),
    path("collection/<slug:slug>/", views.CollectionDetailView.as_view(), name="collection_detail"),
    path("product/<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("wishlist/toggle/<uuid:product_id>/", views.ToggleWishlistView.as_view(), name="toggle_wishlist"),
]

