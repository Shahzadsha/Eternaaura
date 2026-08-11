from catalog.models import Category, Collection, Wishlist


def wishlist_summary(request):
    """
    Injects user_wishlist_ids (set of product UUID strings and objects) and
    wishlist_count into template context on every request.
    """
    if request.user.is_authenticated:
        raw_ids = list(Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True))
        wishlisted_ids = set(raw_ids) | {str(pid) for pid in raw_ids}
        return {
            "user_wishlist_ids": wishlisted_ids,
            "wishlist_count": len(raw_ids),
        }
    return {
        "user_wishlist_ids": set(),
        "wishlist_count": 0,
    }


def nav_categories_processor(request):
    """
    Injects active top-level categories and active collections
    into template context on every request for navigation menus.
    """
    top_categories = (
        Category.objects.filter(is_active=True, parent__isnull=True)
        .prefetch_related("children")
        .order_by("display_order", "name")
    )
    active_collections = Collection.objects.filter(is_active=True).order_by("name")
    return {
        "nav_categories": top_categories,
        "nav_collections": active_collections,
    }


def store_settings_processor(request):
    """
    Injects global store_settings and site_settings into template context
    on every request so Admin Settings changes instantly reflect everywhere.
    """
    from dashboard.models import StoreSettings
    settings_obj = StoreSettings.get_solo()
    return {
        "store_settings": settings_obj,
        "site_settings": settings_obj,
    }

