from django.core.cache import cache
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .context_processors import _fetch_nav_data
from .models import Category, Collection, HeroBanner, Product, RecentlyViewed, Wishlist


def _fetch_homepage_public_data():
    banners = list(HeroBanner.objects.filter(is_active=True).order_by("display_order", "-created_at"))
    new_arrivals = list(
        Product.objects.filter(is_published=True, is_new_arrival=True)
        .select_related("category")
        .prefetch_related("images")[:8]
    )
    best_sellers = list(
        Product.objects.filter(is_published=True, is_best_seller=True)
        .select_related("category")
        .prefetch_related("images")[:8]
    )
    trending = list(
        Product.objects.filter(is_published=True, is_trending=True)
        .select_related("category")
        .prefetch_related("images")[:8]
    )
    active_collections = list(Collection.objects.filter(is_active=True))

    bridal = next((c for c in active_collections if c.slug == "bridal-collection"), None)
    if bridal is None and active_collections:
        bridal = active_collections[0]

    daily_wear = next((c for c in active_collections if c.slug == "daily-wear-collection"), None)
    if daily_wear is None and len(active_collections) > 1:
        daily_wear = active_collections[1]

    return {
        "banners": banners,
        "new_arrivals": new_arrivals,
        "best_sellers": best_sellers,
        "trending": trending,
        "collections": active_collections,
        "bridal": bridal,
        "daily_wear": daily_wear,
    }


class HomeView(TemplateView):
    template_name = "catalog/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        public_data = cache.get_or_set("homepage_public_data", _fetch_homepage_public_data, timeout=300)
        ctx.update(public_data)
        nav_data = cache.get_or_set("nav_categories_data", _fetch_nav_data, timeout=300)
        ctx["categories"] = nav_data.get("nav_categories", [])
        return ctx



def apply_catalog_filtering_and_sorting(queryset, request):
    qs = queryset
    GET = request.GET if hasattr(request, 'GET') else request

    def _get_list(param):
        if hasattr(GET, "getlist"):
            return GET.getlist(param)
        val = GET.get(param)
        if not val:
            return []
        return [val] if isinstance(val, str) else val

    # 1. In Stock filter
    if GET.get("in_stock") == "1":
        qs = qs.filter(stock_quantity__gt=0)

    # 2. Price Range filter
    min_price = GET.get("min_price")
    max_price = GET.get("max_price")
    if min_price:
        try:
            qs = qs.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass
    if max_price:
        try:
            qs = qs.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass

    # 3. Metal Purity filter (supports multiple selections)
    purities = _get_list("purity")
    if purities:
        qs = qs.filter(metal_purity__in=purities)

    # 4. Gemstone filter (supports multiple selections)
    gemstones = _get_list("gemstone")
    if gemstones:
        qs = qs.filter(gemstone__in=gemstones)

    # 5. Rating filter
    min_rating = GET.get("min_rating")
    if min_rating:
        try:
            qs = qs.filter(average_rating__gte=float(min_rating))
        except (ValueError, TypeError):
            pass

    # 6. Sorting
    sort_param = GET.get("sort", "")
    sort_map = {
        "newest": "-created_at",
        "oldest": "created_at",
        "price_low": "price",
        "price_high": "-price",
        "popularity": ("-is_best_seller", "-review_count", "-created_at"),
        "best_sellers": ("-is_best_seller", "-created_at"),
        "trending": ("-is_trending", "-created_at"),
        "rating": ("-average_rating", "-review_count", "-created_at"),
        "reviews": ("-review_count", "-average_rating", "-created_at"),
        "discount_high": ("-compare_at_price", "-created_at"),
        "name_asc": "name",
        "name_desc": "-name",
    }
    ordering = sort_map.get(sort_param, "-created_at")
    if isinstance(ordering, tuple):
        qs = qs.order_by(*ordering)
    else:
        qs = qs.order_by(ordering)

    return qs


def build_catalog_context(base_qs, request):
    # Fetch available purities & gemstones from base_qs
    purities_raw = list(base_qs.values_list("metal_purity", flat=True).distinct())
    available_purities = [p for p in purities_raw if p]

    gemstones_raw = list(base_qs.values_list("gemstone", flat=True).distinct())
    available_gemstones = [g for g in gemstones_raw if g]

    filtered_qs = apply_catalog_filtering_and_sorting(base_qs, request).select_related("category").prefetch_related("images")

    GET = request.GET if hasattr(request, 'GET') else request

    def _get_list(param):
        if hasattr(GET, "getlist"):
            return GET.getlist(param)
        val = GET.get(param)
        if not val:
            return []
        return [val] if isinstance(val, str) else val

    selected_purities = _get_list("purity")
    selected_gemstones = _get_list("gemstone")

    active_filters = 0
    if GET.get("in_stock") == "1":
        active_filters += 1
    if GET.get("min_price") or GET.get("max_price"):
        active_filters += 1
    if selected_purities:
        active_filters += len(selected_purities)
    if selected_gemstones:
        active_filters += len(selected_gemstones)
    if GET.get("min_rating"):
        active_filters += 1

    return {
        "products": filtered_qs,
        "matching_count": filtered_qs.count(),
        "current_sort": GET.get("sort", "newest"),
        "in_stock_active": GET.get("in_stock") == "1",
        "min_price": GET.get("min_price", ""),
        "max_price": GET.get("max_price", ""),
        "selected_purities": selected_purities,
        "selected_gemstones": selected_gemstones,
        "min_rating": GET.get("min_rating", ""),
        "active_filter_count": active_filters,
        "available_purities": available_purities,
        "available_gemstones": available_gemstones,
    }


def apply_sorting(queryset, sort_param):
    return apply_catalog_filtering_and_sorting(queryset, {"sort": sort_param})


class CategoryDetailView(DetailView):
    model = Category
    template_name = "catalog/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base_qs = self.object.products.filter(is_published=True)
        catalog_ctx = build_catalog_context(base_qs, self.request)
        ctx.update(catalog_ctx)
        return ctx


class CollectionDetailView(DetailView):
    model = Collection
    template_name = "catalog/collection_detail.html"
    context_object_name = "collection"

    def get_queryset(self):
        return Collection.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base_qs = self.object.products.filter(is_published=True)
        catalog_ctx = build_catalog_context(base_qs, self.request)
        ctx.update(catalog_ctx)
        return ctx


class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        qs = Product.objects.select_related("category").prefetch_related("images", "variants", "variants__values")
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            qs = qs.filter(is_published=True)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self.object

        related = Product.objects.filter(
            is_published=True, category=product.category
        ).exclude(pk=product.pk).select_related("category").prefetch_related("images").order_by("-is_best_seller", "-average_rating")[:8]
        manual_related = product.manually_related_products.filter(is_published=True).select_related("category").prefetch_related("images")
        ctx["related_products"] = manual_related if manual_related.exists() else related

        # Fetch sibling color variant products matching exact name AND category
        ctx["color_variant_products"] = Product.objects.filter(
            is_published=True,
            name=product.name,
            category=product.category
        ).prefetch_related("images", "variants", "variants__values").order_by("created_at")

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
            ).exclude(product=product).select_related("product__category").prefetch_related("product__images")[:8]
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
        return apply_catalog_filtering_and_sorting(qs, self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        base_qs = Product.objects.filter(is_published=True)
        if query:
            base_qs = base_qs.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(category__name__icontains=query)
                | Q(sku__iexact=query)
            )
        catalog_ctx = build_catalog_context(base_qs, self.request)
        ctx.update(catalog_ctx)
        ctx["query"] = query
        return ctx


class ToggleWishlistView(View):

    def _is_ajax(self, request):
        return (
            request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"
        )

    def post(self, request, product_id):
        referer = request.META.get("HTTP_REFERER", reverse("catalog:home"))

        if not request.user.is_authenticated:
            if self._is_ajax(request):
                return JsonResponse(
                    {"authenticated": False, "login_url": f"{reverse('accounts:login')}?next={referer}"},
                    status=401,
                )
            return redirect(f"{reverse('accounts:login')}?next={referer}")

        product = get_object_or_404(Product, pk=product_id)
        item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if not created:
            item.delete()

        if self._is_ajax(request):
            wishlist_count = Wishlist.objects.filter(user=request.user).count()
            return JsonResponse({
                "authenticated": True,
                "wishlisted": created,
                "wishlist_count": wishlist_count,
                "count": wishlist_count,
                "product_id": str(product.id),
            })

        return redirect(referer)

    def get(self, request, product_id):
        return self.post(request, product_id)


class BaseShowcaseView(ListView):
    template_name = "catalog/showcase_list.html"
    context_object_name = "products"
    paginate_by = 16

    def get_queryset(self):
        base_qs = Product.objects.filter(is_published=True)
        filtered_base = self.filter_products(base_qs)
        return apply_catalog_filtering_and_sorting(filtered_base, self.request)

    def filter_products(self, qs):
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base_qs = Product.objects.filter(is_published=True)
        filtered_base = self.filter_products(base_qs)
        catalog_ctx = build_catalog_context(filtered_base, self.request)
        ctx.update(catalog_ctx)
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