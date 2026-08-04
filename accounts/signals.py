from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User

ROLE_LABELS = {
    User.StaffRole.SUPER_ADMIN: "Super Admin",
    User.StaffRole.PRODUCT_MANAGER: "Product Manager",
    User.StaffRole.ORDER_MANAGER: "Order Manager",
    User.StaffRole.CUSTOMER_SUPPORT: "Customer Support",
    User.StaffRole.CONTENT_MANAGER: "Content Manager",
    User.StaffRole.MARKETING_MANAGER: "Marketing Manager",
}


@receiver(post_save, sender=User)
def sync_staff_role_group(sender, instance, **kwargs):
    """
    Whenever a user's staff_role changes, put them in the matching Django Group
    (run `manage.py setup_staff_roles` once so those Groups exist with permissions)
    and remove them from the other role groups so access stays exclusive.
    """
    if not instance.is_staff:
        return
    role = instance.staff_role
    if role == User.StaffRole.NONE:
        return
    target_label = ROLE_LABELS.get(role)
    if not target_label:
        return
    try:
        target_group = Group.objects.get(name=target_label)
    except Group.DoesNotExist:
        return  # setup_staff_roles hasn't been run yet — nothing to sync into

    other_labels = [label for r, label in ROLE_LABELS.items() if label != target_label]
    stale_groups = Group.objects.filter(name__in=other_labels, user=instance)
    instance.groups.remove(*stale_groups)
    instance.groups.add(target_group)
