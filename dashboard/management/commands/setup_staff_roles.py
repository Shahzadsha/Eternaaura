from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from accounts.models import User

# Map each staff role to the app_labels/models it should manage.
# Super Admin gets everything and is handled separately (all permissions).
ROLE_MODEL_SCOPE = {
    User.StaffRole.PRODUCT_MANAGER: [
        ("catalog", "product"), ("catalog", "productimage"), ("catalog", "productvariant"),
        ("catalog", "category"), ("catalog", "collection"), ("catalog", "product360view"),
        ("catalog", "productvideo"),
    ],
    User.StaffRole.ORDER_MANAGER: [
        ("orders", "order"), ("orders", "orderitem"), ("orders", "returnrequest"),
        ("payments", "payment"),
    ],
    User.StaffRole.CUSTOMER_SUPPORT: [
        ("orders", "order"), ("orders", "returnrequest"), ("accounts", "user"),
        ("reviews", "review"),
    ],
    User.StaffRole.CONTENT_MANAGER: [
        ("catalog", "herobanner"), ("catalog", "collection"), ("reviews", "review"),
    ],
    User.StaffRole.MARKETING_MANAGER: [
        ("coupons", "coupon"), ("catalog", "herobanner"),
    ],
}

ROLE_LABELS = {
    User.StaffRole.SUPER_ADMIN: "Super Admin",
    User.StaffRole.PRODUCT_MANAGER: "Product Manager",
    User.StaffRole.ORDER_MANAGER: "Order Manager",
    User.StaffRole.CUSTOMER_SUPPORT: "Customer Support",
    User.StaffRole.CONTENT_MANAGER: "Content Manager",
    User.StaffRole.MARKETING_MANAGER: "Marketing Manager",
}


class Command(BaseCommand):
    help = "Create/update Django Groups for each ETERNAAURA staff role with scoped default permissions."

    def handle(self, *args, **options):
        # Super Admin: every permission that exists.
        super_group, _ = Group.objects.get_or_create(name=ROLE_LABELS[User.StaffRole.SUPER_ADMIN])
        super_group.permissions.set(Permission.objects.all())
        self.stdout.write(self.style.SUCCESS(f"✓ {super_group.name}: {super_group.permissions.count()} permissions"))

        for role, scope in ROLE_MODEL_SCOPE.items():
            group, _ = Group.objects.get_or_create(name=ROLE_LABELS[role])
            perms = []
            for app_label, model_name in scope:
                try:
                    ct = ContentType.objects.get(app_label=app_label, model=model_name)
                except ContentType.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"  skip {app_label}.{model_name} — model not found (check app/model name)"
                    ))
                    continue
                perms.extend(Permission.objects.filter(content_type=ct))
            group.permissions.set(perms)
            self.stdout.write(self.style.SUCCESS(f"✓ {group.name}: {group.permissions.count()} permissions"))

        self.stdout.write(self.style.SUCCESS(
            "\nRoles ready. Assign a user to a role via Django admin (User > staff_role + is_staff=True, "
            "then add them to the matching Group), or extend accounts signals to do this automatically."
        ))
