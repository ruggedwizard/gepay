# Generated by Django 4.2.4 on 2024-03-21 19:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dashboard', '0011_remove_transaction_deposit_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_transactions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_transactions', to=settings.AUTH_USER_MODEL),
        ),
    ]
