# Generated by Django 5.1.4 on 2024-12-31 07:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_permissions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='permissions',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
