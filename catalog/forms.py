from django import forms

from .models import Category, Collection, HeroBanner, Product

DARK_INPUT = (
    "w-full rounded-lg bg-panel2 border border-white/10 px-4 py-2.5 text-sm "
    "text-gray-100 focus:outline-none focus:border-gold"
)
DARK_TEXTAREA = DARK_INPUT + " min-h-[100px]"
DARK_SELECT = DARK_INPUT
DARK_CHECKBOX = "rounded bg-panel2 border-white/20 text-gold focus:ring-gold"


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "sku", "category", "collections",
            "short_description", "description",
            "metal_purity", "metal_weight_grams", "gemstone", "gemstone_details",
            "price", "compare_at_price", "stock_quantity", "low_stock_threshold",
            "is_featured", "is_new_arrival", "is_best_seller", "is_trending", "is_published",
            "meta_title", "meta_description",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": DARK_INPUT}),
            "sku": forms.TextInput(attrs={"class": DARK_INPUT}),
            "category": forms.Select(attrs={"class": DARK_SELECT}),
            "collections": forms.SelectMultiple(attrs={"class": DARK_SELECT, "size": 4}),
            "short_description": forms.TextInput(attrs={"class": DARK_INPUT}),
            "description": forms.Textarea(attrs={"class": DARK_TEXTAREA}),
            "metal_purity": forms.Select(attrs={"class": DARK_SELECT}),
            "metal_weight_grams": forms.NumberInput(attrs={"class": DARK_INPUT, "step": "0.001"}),
            "gemstone": forms.TextInput(attrs={"class": DARK_INPUT}),
            "gemstone_details": forms.Textarea(attrs={"class": DARK_TEXTAREA}),
            "price": forms.NumberInput(attrs={"class": DARK_INPUT, "step": "0.01"}),
            "compare_at_price": forms.NumberInput(attrs={"class": DARK_INPUT, "step": "0.01"}),
            "stock_quantity": forms.NumberInput(attrs={"class": DARK_INPUT}),
            "low_stock_threshold": forms.NumberInput(attrs={"class": DARK_INPUT}),
            "meta_title": forms.TextInput(attrs={"class": DARK_INPUT}),
            "meta_description": forms.Textarea(attrs={"class": DARK_TEXTAREA}),
            "is_featured": forms.CheckboxInput(attrs={"class": DARK_CHECKBOX}),
            "is_new_arrival": forms.CheckboxInput(attrs={"class": DARK_CHECKBOX}),
            "is_best_seller": forms.CheckboxInput(attrs={"class": DARK_CHECKBOX}),
            "is_trending": forms.CheckboxInput(attrs={"class": DARK_CHECKBOX}),
            "is_published": forms.CheckboxInput(attrs={"class": DARK_CHECKBOX}),
        }

    def clean_compare_at_price(self):
        compare = self.cleaned_data.get("compare_at_price")
        price = self.cleaned_data.get("price")
        if compare is not None and price is not None and compare <= price:
            raise forms.ValidationError("Compare-at (original) price must be higher than the selling price.")
        return compare


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "image", "parent", "is_active", "display_order",
                  "meta_title", "meta_description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": DARK_INPUT}),
            "description": forms.Textarea(attrs={"class": DARK_TEXTAREA}),
            "image": forms.ClearableFileInput(attrs={"class": DARK_INPUT}),
            "parent": forms.Select(attrs={"class": DARK_SELECT}),
            "display_order": forms.NumberInput(attrs={"class": DARK_INPUT}),
            "meta_title": forms.TextInput(attrs={"class": DARK_INPUT}),
            "meta_description": forms.Textarea(attrs={"class": DARK_TEXTAREA}),
            "is_active": forms.CheckboxInput(attrs={"class": DARK_CHECKBOX}),
        }


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["name", "slug", "description", "banner_image", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": DARK_INPUT, "placeholder": "e.g. Royal Bridal Heritage"}),
            "slug": forms.TextInput(attrs={"class": DARK_INPUT, "placeholder": "e.g. royal-bridal-heritage (auto-generated if blank)"}),
            "description": forms.Textarea(attrs={"class": DARK_TEXTAREA, "rows": 4, "placeholder": "Crafted for timeless elegance and modern royalty..."}),
            "banner_image": forms.ClearableFileInput(attrs={"class": DARK_INPUT, "accept": "image/*"}),
            "is_active": forms.CheckboxInput(attrs={"class": DARK_CHECKBOX}),
        }


from coupons.models import Coupon


class HeroBannerForm(forms.ModelForm):
    class Meta:
        model = HeroBanner
        fields = ["title", "subtitle", "image", "display_order", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"class": DARK_INPUT}),
            "subtitle": forms.TextInput(attrs={"class": DARK_INPUT}),
            "image": forms.ClearableFileInput(attrs={"class": DARK_INPUT}),
            "display_order": forms.NumberInput(attrs={"class": DARK_INPUT}),
            "is_active": forms.CheckboxInput(attrs={"class": DARK_CHECKBOX}),
        }


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            "code", "description", "discount_type", "discount_value",
            "min_order_value", "max_discount_amount", "usage_limit",
            "user_limit", "valid_from", "valid_until", "is_active",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": DARK_INPUT + " uppercase font-mono tracking-wider", "placeholder": "e.g. ETERNA20"}),
            "description": forms.TextInput(attrs={"class": DARK_INPUT, "placeholder": "e.g. 20% off on all bridal jewellery"}),
            "discount_type": forms.Select(attrs={"class": DARK_SELECT}),
            "discount_value": forms.NumberInput(attrs={"class": DARK_INPUT, "step": "0.01", "placeholder": "e.g. 20"}),
            "min_order_value": forms.NumberInput(attrs={"class": DARK_INPUT, "step": "0.01", "placeholder": "0"}),
            "max_discount_amount": forms.NumberInput(attrs={"class": DARK_INPUT, "step": "0.01", "placeholder": "Optional cap"}),
            "usage_limit": forms.NumberInput(attrs={"class": DARK_INPUT, "placeholder": "Optional total limit"}),
            "user_limit": forms.NumberInput(attrs={"class": DARK_INPUT, "placeholder": "Limit per user (default 1)"}),
            "valid_from": forms.DateTimeInput(attrs={"class": DARK_INPUT, "type": "datetime-local"}),
            "valid_until": forms.DateTimeInput(attrs={"class": DARK_INPUT, "type": "datetime-local"}),
            "is_active": forms.CheckboxInput(attrs={"class": DARK_CHECKBOX}),
        }
