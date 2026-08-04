import uuid
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStamped):
    """Necklaces, Earrings, Rings, Bangles, Bracelets, Anklets, Watches,
    Nose Pins, Chains, Pendants, Jewellery Boxes, etc."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["display_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:category_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


class Collection(TimeStamped):
    """Bridal Collection, Daily Wear, Trending, New Arrivals (curated), etc."""
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    banner_image = models.ImageField(upload_to="collections/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(TimeStamped):
    class MetalPurity(models.TextChoices):
        K14 = "14k", "14K Gold"
        K18 = "18k", "18K Gold"
        K22 = "22k", "22K Gold"
        K24 = "24k", "24K Gold"
        SILVER_925 = "silver925", "Sterling Silver 925"
        PLATINUM = "platinum", "Platinum"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    collections = models.ManyToManyField(Collection, blank=True, related_name="products")

    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    specifications = models.JSONField(default=dict, blank=True)  # {"Clasp": "Lobster", ...}

    # Jewellery-specific attributes
    metal_purity = models.CharField(max_length=20, choices=MetalPurity.choices, blank=True)
    metal_weight_grams = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    gemstone = models.CharField(max_length=120, blank=True)
    gemstone_details = models.TextField(blank=True)

    price = models.DecimalField(max_digits=12, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)

    manually_related_products = models.ManyToManyField("self", blank=True, symmetrical=False)

    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_published", "is_featured"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:220]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    @property
    def discount_percent(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return round((1 - self.price / self.compare_at_price) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity <= self.low_stock_threshold

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.product.name} image #{self.display_order}"


class Product360View(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="view_360")
    frame_folder_url = models.CharField(max_length=300, help_text="Base URL/path holding sequential 360 frames")
    frame_count = models.PositiveIntegerField(default=36)


class ProductVideo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="videos")
    video = models.FileField(upload_to="products/videos/")
    thumbnail = models.ImageField(upload_to="products/video_thumbs/", blank=True, null=True)


class VariantAttribute(models.Model):
    """e.g. Size, Color, Material — used to build ProductVariant combinations."""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class VariantValue(models.Model):
    attribute = models.ForeignKey(VariantAttribute, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=50)

    class Meta:
        unique_together = ("attribute", "value")

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductVariant(TimeStamped):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku_suffix = models.CharField(max_length=40)
    values = models.ManyToManyField(VariantValue, related_name="variants")
    price_override = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    @property
    def effective_price(self):
        return self.price_override if self.price_override is not None else self.product.price

    def __str__(self):
        return f"{self.product.name} ({self.sku_suffix})"


class Wishlist(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")


class RecentlyViewed(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="recently_viewed", null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-viewed_at"]


class HeroBanner(TimeStamped):
    """Auto-sliding homepage carousel slides — fully admin-managed."""
    title = models.CharField(max_length=150)
    subtitle = models.CharField(max_length=250, blank=True)
    image = models.ImageField(upload_to="banners/")
    cta_label = models.CharField(max_length=50, default="Shop Now")
    cta_url = models.CharField(max_length=300, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.title
