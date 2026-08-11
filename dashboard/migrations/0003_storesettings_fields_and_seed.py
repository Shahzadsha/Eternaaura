import os
from django.db import migrations, models


def seed_store_settings(apps, schema_editor):
    StoreSettings = apps.get_model('dashboard', 'StoreSettings')
    merchant_upi_id = os.environ.get("MERCHANT_UPI_ID", "")
    merchant_name = os.environ.get("MERCHANT_NAME", "")
    whatsapp_notify_number = os.environ.get("WHATSAPP_NOTIFY_NUMBER", "")

    obj, _ = StoreSettings.objects.get_or_create(pk=1)
    if merchant_upi_id and not obj.merchant_upi_id:
        obj.merchant_upi_id = merchant_upi_id
    if merchant_name and not obj.merchant_name:
        obj.merchant_name = merchant_name
    if whatsapp_notify_number and not obj.whatsapp_notify_number:
        obj.whatsapp_notify_number = whatsapp_notify_number
    obj.save()


def reverse_seed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_storesetting'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='StoreSetting',
            new_name='StoreSettings',
        ),
        migrations.AlterModelOptions(
            name='storesettings',
            options={'verbose_name': 'Store Setting', 'verbose_name_plural': 'Store Settings'},
        ),
        migrations.AddField(
            model_name='storesettings',
            name='merchant_upi_id',
            field=models.CharField(blank=True, default='', help_text='UPI VPA ID for accepting payments (e.g. merchant@upi)', max_length=255),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='merchant_name',
            field=models.CharField(blank=True, default='', help_text='Registered Merchant Name displayed on UPI apps', max_length=255),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='whatsapp_notify_number',
            field=models.CharField(blank=True, default='', help_text='WhatsApp phone number (with country code) for order notifications', max_length=50),
        ),
        migrations.RunPython(seed_store_settings, reverse_code=reverse_seed),
    ]
