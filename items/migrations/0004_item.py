# Generated by Django 5.1.4 on 2025-01-01 09:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0003_alter_customer_email_alter_customer_phone_number'),
        ('items', '0003_alter_fleet_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial_number', models.CharField(max_length=100, unique=True)),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='clients.customer')),
                ('fleet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='items.fleet')),
                ('manufacturers', models.ManyToManyField(blank=True, related_name='items', to='items.manufacturer')),
            ],
        ),
    ]
