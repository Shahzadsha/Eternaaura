from django.core.cache import cache
from catalog.models import Category, Collection, Wishlist


def wishlist_summary(request):
    """
    Injects user_wishlist_ids (set of product UUID strings and objects) and
    wishlist_count into template context on every request for authenticated users.
    User data is NEVER stored in shared cache.
    """
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        raw_ids = list(Wishlist.objects.filter(user=user).values_list("product_id", flat=True))
        wishlisted_ids = set(raw_ids) | {str(pid) for pid in raw_ids}
        return {
            "user_wishlist_ids": wishlisted_ids,
            "wishlist_count": len(raw_ids),
        }
    return {
        "user_wishlist_ids": set(),
        "wishlist_count": 0,
    }


def _fetch_nav_data():
    top_categories = list(
        Category.objects.filter(is_active=True, parent__isnull=True)
        .prefetch_related("children")
        .order_by("display_order", "name")
    )
    active_collections = list(Collection.objects.filter(is_active=True).order_by("name"))
    return {
        "nav_categories": top_categories,
        "nav_collections": active_collections,
    }


def nav_categories_processor(request):
    """
    Injects active top-level categories and active collections
    into template context for navigation menus using 5-minute low-level caching.
    """
    nav_data = cache.get_or_set("nav_categories_data", _fetch_nav_data, timeout=300)
    return nav_data


def store_settings_processor(request):
    """
    Injects global store_settings into template context using 5-minute low-level caching.
    """
    from dashboard.models import StoreSettings
    settings_obj = cache.get_or_set("global_store_settings", StoreSettings.get_solo, timeout=300)
    return {
        "store_settings": settings_obj,
        "site_settings": settings_obj,
    }
