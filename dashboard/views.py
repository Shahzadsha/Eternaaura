from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from catalog.forms import CategoryForm, HeroBannerForm, ProductForm
from catalog.models import Category, HeroBanner, Product, ProductImage
from orders.models import Order


class StaffLoginView(LoginView):
    """Only page under /staff/ reachable without an existing staff session.
    Never linked from customer-facing templates."""
    template_name = "dashboard/login.html"

    def get_success_url(self):
        return "/staff/"


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "dashboard:login"

    def test_func(self):
        return self.request.user.is_staff


class StaffPermissionMixin(StaffRequiredMixin, PermissionRequiredMixin):
    """Staff must be logged in AND hold the specific model permission for this
    action. Superusers and the Super Admin group (all perms) always pass.
    Other roles only pass for the models `setup_staff_roles` scoped to them."""
    raise_exception = False

    def handle_no_permission(self):
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            return super().handle_no_permission()
        messages.error(self.request, "Your staff role doesn't have permission for that action.")
        return redirect("dashboard:home")


class DashboardHomeView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()
        ctx["total_products"] = Product.objects.count()
        ctx["low_stock_products"] = Product.objects.filter(
            stock_quantity__lte=5, stock_quantity__gt=0
        )
        ctx["orders_today"] = Order.objects.filter(placed_at__date=today).count()
        ctx["revenue_today"] = Order.objects.filter(placed_at__date=today).aggregate(
            total=Sum("grand_total")
        )["total"] or 0
        ctx["orders_by_status"] = Order.objects.values("status").annotate(count=Count("id"))
        return ctx


class OrderManagementView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/orders.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["orders"] = Order.objects.all().select_related("user")
        return ctx


from django.db.models.functions import TruncDate
from django.http import JsonResponse

class AnalyticsView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()
        valid_statuses = [
            Order.Status.CONFIRMED,
            Order.Status.PROCESSING,
            Order.Status.SHIPPED,
            Order.Status.OUT_FOR_DELIVERY,
            Order.Status.DELIVERED,
        ]
        ctx["total_confirmed_orders"] = Order.objects.filter(status__in=valid_statuses).count()
        ctx["total_lifetime_revenue"] = Order.objects.filter(status__in=valid_statuses).aggregate(
            total=Sum("grand_total")
        )["total"] or 0
        return ctx


class DailyRevenueApiView(StaffRequiredMixin, View):
    """
    Returns JSON daily revenue histogram data and mean average line.
    Used by Chart.js in the staff console for real-time analytics.
    """
    def get(self, request):
        days = int(request.GET.get("days", 14))
        days = max(7, min(90, days))
        start_date = timezone.now().date() - timezone.timedelta(days=days - 1)

        valid_statuses = [
            Order.Status.CONFIRMED,
            Order.Status.PROCESSING,
            Order.Status.SHIPPED,
            Order.Status.OUT_FOR_DELIVERY,
            Order.Status.DELIVERED,
        ]

        orders_qs = Order.objects.filter(
            status__in=valid_statuses,
            placed_at__date__gte=start_date
        )

        revenue_by_day = dict(
            orders_qs.annotate(day=TruncDate("placed_at"))
            .values("day")
            .annotate(total=Sum("grand_total"))
            .values_list("day", "total")
        )

        labels = []
        date_strings = []
        revenues = []

        current_date = start_date
        today = timezone.now().date()

        while current_date <= today:
            val = float(revenue_by_day.get(current_date) or 0)
            labels.append(current_date.strftime("%b %d"))
            date_strings.append(current_date.strftime("%Y-%m-%d"))
            revenues.append(round(val, 2))
            current_date += timezone.timedelta(days=1)

        has_data = any(r > 0 for r in revenues)
        total_revenue = sum(revenues)
        avg_revenue = total_revenue / len(revenues) if revenues else 0.0

        return JsonResponse({
            "has_data": has_data,
            "days": len(revenues),
            "labels": labels,
            "date_strings": date_strings,
            "revenues": revenues,
            "average_daily_revenue": round(avg_revenue, 2),
            "total_period_revenue": round(total_revenue, 2),
            "average_line": [round(avg_revenue, 2)] * len(revenues),
        })


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

class ProductManagementView(StaffRequiredMixin, ListView):
    template_name = "dashboard/products.html"
    context_object_name = "products"

    def get_queryset(self):
        return Product.objects.all().select_related("category")


class ProductCreateView(StaffPermissionMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "dashboard/product_form.html"
    permission_required = "catalog.add_product"
    success_url = reverse_lazy("dashboard:products")

    def form_valid(self, form):
        response = super().form_valid(form)
        self._save_uploaded_images()
        messages.success(self.request, f'"{self.object.name}" was created.')
        return response

    def _save_uploaded_images(self):
        files = self.request.FILES.getlist("images")
        for i, f in enumerate(files):
            ProductImage.objects.create(
                product=self.object, image=f,
                display_order=i, is_primary=(i == 0 and not self.object.images.exists()),
            )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        return ctx


class ProductUpdateView(StaffPermissionMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "dashboard/product_form.html"
    permission_required = "catalog.change_product"
    success_url = reverse_lazy("dashboard:products")

    def form_valid(self, form):
        response = super().form_valid(form)
        files = self.request.FILES.getlist("images")
        start = self.object.images.count()
        for i, f in enumerate(files):
            ProductImage.objects.create(
                product=self.object, image=f,
                display_order=start + i, is_primary=(start == 0 and i == 0),
            )
        messages.success(self.request, f'"{self.object.name}" was updated.')
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["existing_images"] = self.object.images.all()
        return ctx


class ProductDeleteView(StaffPermissionMixin, DeleteView):
    model = Product
    permission_required = "catalog.delete_product"
    success_url = reverse_lazy("dashboard:products")
    template_name = "dashboard/confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f'Delete "{self.object.name}"?'
        ctx["cancel_url"] = reverse_lazy("dashboard:products")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'"{self.object.name}" was deleted.')
        return super().form_valid(form)


class ProductTogglePublishView(StaffPermissionMixin, View):
    permission_required = "catalog.change_product"

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.is_published = not product.is_published
        product.save(update_fields=["is_published"])
        messages.success(request, f'"{product.name}" is now {"published" if product.is_published else "a draft"}.')
        return redirect("dashboard:products")


class ProductImageDeleteView(StaffPermissionMixin, View):
    permission_required = "catalog.change_product"

    def post(self, request, pk, image_id):
        image = get_object_or_404(ProductImage, pk=image_id, product_id=pk)
        image.delete()
        messages.success(request, "Image removed.")
        return redirect("dashboard:product_edit", pk=pk)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

class CategoryManagementView(StaffRequiredMixin, ListView):
    model = Category
    template_name = "dashboard/categories.html"
    context_object_name = "categories"


class CategoryCreateView(StaffPermissionMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "dashboard/category_form.html"
    permission_required = "catalog.add_category"
    success_url = reverse_lazy("dashboard:categories")

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" was created.')
        return super().form_valid(form)


class CategoryUpdateView(StaffPermissionMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "dashboard/category_form.html"
    permission_required = "catalog.change_category"
    success_url = reverse_lazy("dashboard:categories")

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" was updated.')
        return super().form_valid(form)


class CategoryDeleteView(StaffPermissionMixin, DeleteView):
    model = Category
    permission_required = "catalog.delete_category"
    success_url = reverse_lazy("dashboard:categories")
    template_name = "dashboard/confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f'Delete "{self.object.name}"?'
        ctx["cancel_url"] = reverse_lazy("dashboard:categories")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'"{self.object.name}" was deleted.')
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Homepage banners
# ---------------------------------------------------------------------------

class BannerManagementView(StaffRequiredMixin, ListView):
    model = HeroBanner
    template_name = "dashboard/banners.html"
    context_object_name = "banners"


class BannerCreateView(StaffPermissionMixin, CreateView):
    model = HeroBanner
    form_class = HeroBannerForm
    template_name = "dashboard/banner_form.html"
    permission_required = "catalog.add_herobanner"
    success_url = reverse_lazy("dashboard:banners")

    def form_valid(self, form):
        messages.success(self.request, "Banner created.")
        return super().form_valid(form)


class BannerUpdateView(StaffPermissionMixin, UpdateView):
    model = HeroBanner
    form_class = HeroBannerForm
    template_name = "dashboard/banner_form.html"
    permission_required = "catalog.change_herobanner"
    success_url = reverse_lazy("dashboard:banners")

    def form_valid(self, form):
        messages.success(self.request, "Banner updated.")
        return super().form_valid(form)


class BannerDeleteView(StaffPermissionMixin, DeleteView):
    model = HeroBanner
    permission_required = "catalog.delete_herobanner"
    success_url = reverse_lazy("dashboard:banners")
    template_name = "dashboard/confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f'Delete "{self.object.title}"?'
        ctx["cancel_url"] = reverse_lazy("dashboard:banners")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Banner deleted.")
        return super().form_valid(form)
