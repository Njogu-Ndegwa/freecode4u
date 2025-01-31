# Generated by Django 5.1.4 on 2025-01-01 06:59

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Fleet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('assigned_agent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_fleets', to=settings.AUTH_USER_MODEL)),
                ('distributor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fleets', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
