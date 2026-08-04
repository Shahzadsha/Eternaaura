from decimal import Decimal

from django.core.management.base import BaseCommand

from catalog.models import Category, Collection, HeroBanner, Product

CATEGORIES = [
    "Necklaces", "Earrings", "Rings", "Bangles", "Bracelets",
    "Anklets", "Watches", "Nose Pins", "Chains", "Pendants", "Jewellery Boxes",
]

COLLECTIONS = [
    ("Bridal Collection", "bridal-collection"),
    ("Daily Wear Collection", "daily-wear-collection"),
]

PRODUCTS = [
    ("Aurelia Diamond Solitaire Ring", "Rings", "18k", "Diamond", 89999, 109999, True, False, True),
    ("Meera Antique Gold Necklace Set", "Necklaces", "22k", "", 154999, 179999, True, True, False),
    ("Ivy Rose Gold Hoop Earrings", "Earrings", "14k", "", 18999, 22999, False, True, True),
    ("Zara Kundan Bridal Choker", "Necklaces", "22k", "Kundan, Polki", 249999, 289999, True, False, False),
    ("Elan Everyday Chain Bracelet", "Bracelets", "18k", "", 24999, None, False, False, True),
    ("Noor Diamond Tennis Bracelet", "Bracelets", "18k", "Diamond", 129999, 149999, True, False, False),
    ("Kiara Pearl Drop Pendant", "Pendants", "14k", "Freshwater Pearl", 15999, 18999, False, True, False),
    ("Vera Classic Gold Bangles (Set of 2)", "Bangles", "22k", "", 68999, None, False, True, True),
]


class Command(BaseCommand):
    help = "Seed ETERNAAURA with demo categories, collections, banners, and products for local preview."

    def handle(self, *args, **options):
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
            title="Timeless Gold, Redefined",
            defaults={"subtitle": "Discover the new gold collection", "image": "", "display_order": 1},
        )
        HeroBanner.objects.get_or_create(
            title="The Bridal Edit",
            defaults={"subtitle": "Heirlooms for your forever day", "image": "", "display_order": 2},
        )
        self.stdout.write(self.style.SUCCESS("✓ hero banners ready"))

        count = 0
        for name, cat_name, purity, gem, price, compare, feat, new, best in PRODUCTS:
            sku = "EA-" + "".join(w[0] for w in name.split())[:8].upper()
            product, created = Product.objects.get_or_create(
                name=name,
                defaults=dict(
                    sku=sku,
                    category=cats[cat_name],
                    metal_purity=purity,
                    gemstone=gem,
                    price=Decimal(price),
                    compare_at_price=Decimal(compare) if compare else None,
                    stock_quantity=12,
                    is_featured=feat,
                    is_new_arrival=new,
                    is_best_seller=best,
                    is_trending=feat or best,
                    short_description=f"Handcrafted {cat_name.lower()[:-1]} in {purity or 'premium metal'}.",
                    description=f"The {name} is crafted by ETERNAAURA's master artisans, "
                                f"blending timeless design with everyday elegance.",
                ),
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"✓ {count} demo products created"))
        self.stdout.write(self.style.SUCCESS("Demo data seeded. Run the server and visit /"))
