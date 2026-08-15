from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Category, Collection, HeroBanner, Product, ProductImage
from dashboard.models import StoreSettings


@receiver([post_save, post_delete], sender=HeroBanner)
@receiver([post_save, post_delete], sender=Product)
@receiver([post_save, post_delete], sender=Collection)
@receiver([post_save, post_delete], sender=Category)
@receiver([post_save, post_delete], sender=ProductImage)
def invalidate_homepage_and_nav_cache(sender, **kwargs):
    cache.delete("homepage_public_data")
    cache.delete("nav_categories_data")


@receiver([post_save, post_delete], sender=StoreSettings)
def invalidate_store_settings_cache(sender, **kwargs):
    cache.delete("global_store_settings")
