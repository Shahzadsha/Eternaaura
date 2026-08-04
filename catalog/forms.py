from django import forms

from .models import Category, HeroBanner, Product

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


class HeroBannerForm(forms.ModelForm):
    class Meta:
        model = HeroBanner
        fields = ["title", "subtitle", "image", "cta_label", "cta_url", "display_order", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"class": DARK_INPUT}),
            "subtitle": forms.TextInput(attrs={"class": DARK_INPUT}),
            "image": forms.ClearableFileInput(attrs={"class": DARK_INPUT}),
            "cta_label": forms.TextInput(attrs={"class": DARK_INPUT}),
            "cta_url": forms.TextInput(attrs={"class": DARK_INPUT}),
            "display_order": forms.NumberInput(attrs={"class": DARK_INPUT}),
            "is_active": forms.CheckboxInput(attrs={"class": DARK_CHECKBOX}),
        }
