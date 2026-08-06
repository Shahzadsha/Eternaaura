from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .models import Category, Collection, HeroBanner, Product, RecentlyViewed, Wishlist


class HomeView(TemplateView):
    template_name = "catalog/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["banners"] = HeroBanner.objects.filter(is_active=True)
        ctx["categories"] = Category.objects.filter(is_active=True, parent__isnull=True)
        ctx["new_arrivals"] = Product.objects.filter(is_published=True, is_new_arrival=True)[:8]
        ctx["best_sellers"] = Product.objects.filter(is_published=True, is_best_seller=True)[:8]
        ctx["trending"] = Product.objects.filter(is_published=True, is_trending=True)[:8]
        ctx["bridal"] = Collection.objects.filter(slug="bridal-collection").first()
        ctx["daily_wear"] = Collection.objects.filter(slug="daily-wear-collection").first()
        return ctx


def apply_sorting(queryset, sort_param):
    sort_map = {
        "newest": "-created_at",
        "oldest": "created_at",
        "price_low": "price",
        "price_high": "-price",
        "best_sellers": ("-is_best_seller", "-created_at"),
        "trending": ("-is_trending", "-created_at"),
        "rating": ("-average_rating", "-review_count", "-created_at"),
        "reviews": ("-review_count", "-average_rating", "-created_at"),
        "name_asc": "name",
        "name_desc": "-name",
        "name": "name",
    }
    ordering = sort_map.get(sort_param, "-created_at")
    if isinstance(ordering, tuple):
        return queryset.order_by(*ordering)
    return queryset.order_by(ordering)


class CategoryDetailView(DetailView):
    model = Category
    template_name = "catalog/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.object.products.filter(is_published=True)
        sort = self.request.GET.get("sort", "")
        ctx["products"] = apply_sorting(qs, sort)
        ctx["current_sort"] = sort
        return ctx


class CollectionDetailView(DetailView):
    model = Collection
    template_name = "catalog/collection_detail.html"
    context_object_name = "collection"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.object.products.filter(is_published=True)
        sort = self.request.GET.get("sort", "")
        ctx["products"] = apply_sorting(qs, sort)
        ctx["current_sort"] = sort
        return ctx


class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        qs = Product.objects.all()
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            qs = qs.filter(is_published=True)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self.object

        related = Product.objects.filter(
            is_published=True, category=product.category
        ).exclude(pk=product.pk).order_by("-is_best_seller", "-average_rating")[:8]
        manual_related = product.manually_related_products.filter(is_published=True)
        ctx["related_products"] = manual_related if manual_related.exists() else related

        review_sort = self.request.GET.get("review_sort", "newest")
        reviews_qs = product.reviews.filter(is_approved=True).select_related("user").prefetch_related("images")
        if review_sort in ["rating_high", "highest_rated"]:
            reviews_qs = reviews_qs.order_by("-rating", "-created_at")
        elif review_sort in ["rating_low", "lowest_rated"]:
            reviews_qs = reviews_qs.order_by("rating", "-created_at")
        elif review_sort in ["helpful", "most_helpful"]:
            reviews_qs = reviews_qs.order_by("-helpful_count", "-created_at")
        elif review_sort == "oldest":
            reviews_qs = reviews_qs.order_by("created_at")
        else:
            reviews_qs = reviews_qs.order_by("-created_at")

        from django.core.paginator import Paginator
        paginator = Paginator(reviews_qs, 10)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        ctx["reviews"] = page_obj
        ctx["reviews_page_obj"] = page_obj
        ctx["reviews_paginator"] = paginator
        ctx["is_reviews_paginated"] = page_obj.has_other_pages()
        ctx["review_sort"] = review_sort
        ctx["questions"] = product.questions.prefetch_related("answers")

        if self.request.user.is_authenticated:
            RecentlyViewed.objects.update_or_create(user=self.request.user, product=product)
            ctx["recently_viewed"] = RecentlyViewed.objects.filter(
                user=self.request.user
            ).exclude(product=product)[:8]
            ctx["is_wishlisted"] = Wishlist.objects.filter(user=self.request.user, product=product).exists()
        return ctx


class SearchView(ListView):
    template_name = "catalog/search_results.html"
    context_object_name = "products"
    paginate_by = 24

    def get_queryset(self):
        query = self.request.GET.get("q", "").strip()
        qs = Product.objects.filter(is_published=True)
        if query:
            qs = qs.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(category__name__icontains=query)
                | Q(sku__iexact=query)
            )
        sort = self.request.GET.get("sort", "")
        return apply_sorting(qs, sort)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_sort"] = self.request.GET.get("sort", "")
        ctx["query"] = self.request.GET.get("q", "").strip()
        return ctx


class ToggleWishlistView(View):

    def post(self, request, product_id):
        referer = request.META.get("HTTP_REFERER", reverse("catalog:home"))
        if not request.user.is_authenticated:
            return redirect(f"{reverse('accounts:login')}?next={referer}")

        product = get_object_or_404(Product, pk=product_id)
        item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if not created:
            item.delete()

        return redirect(referer)

    def get(self, request, product_id):
        return self.post(request, product_id)


class BaseShowcaseView(ListView):
    template_name = "catalog/showcase_list.html"
    context_object_name = "products"
    paginate_by = 16

    def get_queryset(self):
        qs = Product.objects.filter(is_published=True)
        qs = self.filter_products(qs)
        sort = self.request.GET.get("sort", "")
        return apply_sorting(qs, sort)

    def filter_products(self, qs):
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_sort"] = self.request.GET.get("sort", "")
        return ctx


class NewArrivalsView(BaseShowcaseView):
    def filter_products(self, qs):
        filtered = qs.filter(is_new_arrival=True)
        return filtered if filtered.exists() else qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "New Arrivals"
        ctx["page_subtitle"] = "Be the first to discover our latest fine jewellery creations, handcrafted by master artisans."
        ctx["breadcrumb_title"] = "New Arrivals"
        return ctx


class BestSellersView(BaseShowcaseView):
    def filter_products(self, qs):
        filtered = qs.filter(is_best_seller=True)
        return filtered if filtered.exists() else qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Best Sellers"
        ctx["page_subtitle"] = "Our most cherished and iconic pieces, loved by connoisseurs of fine gold and diamonds."
        ctx["breadcrumb_title"] = "Best Sellers"
        return ctx


class TrendingCollectionsView(BaseShowcaseView):
    def filter_products(self, qs):
        filtered = qs.filter(is_trending=True)
        return filtered if filtered.exists() else qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Trending Collections"
        ctx["page_subtitle"] = "Explore today's most sought-after designs and seasonal high-jewellery highlights."
        ctx["breadcrumb_title"] = "Trending Collections"
        return ctx
