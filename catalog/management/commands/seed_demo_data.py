from decimal import Decimal
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.models import Category, Collection, HeroBanner, Product

CATEGORIES = [
    "Earrings", "Necklaces", "Rings", "Bracelets", "Bangles",
    "Anklets", "Chains", "Pendants", "Gift Sets & Hampers", "Jewellery Boxes",
]

COLLECTIONS = [
    ("Anti-Tarnish Essentials", "anti-tarnish-essentials"),
    ("Daily Wear Collection", "daily-wear-collection"),
    ("Gifting & Festive Hampers", "gifting-festive-hampers"),
]

PRODUCTS = [
    # (name, category, price, compare_at_price, is_featured, is_new, is_best, specs)
    (
        "Aura Waterproof Anti-Tarnish Gold Hoop Earrings",
        "Earrings",
        249, 499,
        True, False, True,
        {"Anti-Tarnish": "Yes", "Material": "Stainless Steel with 18K Gold PVD Coating", "Waterproof": "Yes", "Care": "Wipe with dry microfiber cloth"}
    ),
    (
        "Petal Dainty Gold Choker Necklace",
        "Necklaces",
        199, 399,
        True, True, False,
        {"Anti-Tarnish": "Yes", "Material": "18K Gold Plated Brass", "Length": "38cm + 5cm extension", "Clasp": "Lobster"}
    ),
    (
        "Minimalist Adjustable Stackable Ring Set",
        "Rings",
        149, 299,
        False, True, True,
        {"Anti-Tarnish": "No", "Material": "Alloy with High-Lustre Gold Polish", "Size": "Adjustable (Free Size)"}
    ),
    (
        "Eternal Elegance Luxury Gift Hamper Box",
        "Gift Sets & Hampers",
        999, 1499,
        True, False, False,
        {"Gift Pick": "Yes", "Contains": "1x Anti-Tarnish Necklace, 1x Pair Studs, 1x Velvet Keepsake Box, 1x Greeting Card", "Occasion": "Birthday, Anniversary, Festive"}
    ),
    (
        "Gleam Paperclip Chain Link Bracelet",
        "Bracelets",
        199, 349,
        False, False, True,
        {"Anti-Tarnish": "Yes", "Material": "Hypoallergenic Stainless Steel with Gold Finish", "Waterproof": "Yes"}
    ),
    (
        "Solitaire Zircon Pendant with Chain",
        "Pendants",
        299, 599,
        True, False, False,
        {"Anti-Tarnish": "Yes", "Material": "18K Gold Plated Alloy", "Gemstone": "AAA Cubic Zirconia", "Chain Length": "45cm"}
    ),
    (
        "Celestial Starburst Drop Earrings",
        "Earrings",
        179, 349,
        False, True, False,
        {"Anti-Tarnish": "No", "Material": "Gold-Toned Alloy with Micro-Zircons", "Backing": "Push-Back"}
    ),
    (
        "Festive Glam Festive Gift Box",
        "Gift Sets & Hampers",
        1299, 1999,
        True, True, True,
        {"Gift Pick": "Yes", "Contains": "2x Jewellery Sets, 1x Premium Scented Candle, 1x Keepsake Box", "Occasion": "Festive, Wedding Favors"}
    ),
]


class Command(BaseCommand):
    help = "Seed ETERNAAURA with demo categories, collections, banners, and affordable fashion jewellery products."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force-demo",
            action="store_true",
            help="Force seeding even if running outside local development.",
        )

    def handle(self, *args, **options):
        force = options.get("force_demo", False)

        # Safeguard against accidental execution in production
        if not settings.DEBUG and not force:
            raise CommandError(
                "Refusing to seed demo data in a non-DEBUG environment without --force-demo."
            )

        cats = {}
        for i, name in enumerate(CATEGORIES):
            cat, _ = Category.objects.get_or_create(name=name, defaults={"display_order": i})
            cats[name] = cat
        self.stdout.write(self.style.SUCCESS(f"✓ {len(cats)} categories ready"))

        cols = {}
        for name, slug in COLLECTIONS:
            col, _ = Collection.objects.get_or_create(name=name, slug=slug)
            cols[slug] = col
        self.stdout.write(self.style.SUCCESS(f"✓ {len(cols)} collections ready"))

        HeroBanner.objects.get_or_create(
            title="Everyday Anti-Tarnish Jewellery",
            defaults={"subtitle": "Waterproof, hypoallergenic & under ₹299", "image": "", "display_order": 1},
        )
        HeroBanner.objects.get_or_create(
            title="Curated Gift Hampers & Sets",
            defaults={"subtitle": "Gift-ready luxury boxes for your loved ones", "image": "", "display_order": 2},
        )
        self.stdout.write(self.style.SUCCESS("✓ hero banners ready"))

        count = 0
        for name, cat_name, price, compare, feat, new, best, specs in PRODUCTS:
            sku = "EA-" + "".join(w[0] for w in name.split())[:8].upper()
            product, created = Product.objects.get_or_create(
                name=name,
                defaults=dict(
                    sku=sku,
                    category=cats[cat_name],
                    price=Decimal(price),
                    compare_at_price=Decimal(compare) if compare else None,
                    stock_quantity=25,
                    is_featured=feat,
                    is_new_arrival=new,
                    is_best_seller=best,
                    is_trending=feat or best,
                    specifications=specs,
                    short_description=f"Trendy, lightweight {cat_name.lower()} designed for daily styling.",
                    description=f"The {name} brings effortless chic and modern style to your daily wardrobe. "
                                f"Crafted with durable materials and trendsetting aesthetics at an affordable price point.",
                ),
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"✓ {count} demo products created"))
        self.stdout.write(self.style.SUCCESS("Demo data seeded. Run the server and visit /"))
