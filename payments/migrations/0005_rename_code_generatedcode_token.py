# Generated by Django 5.1.4 on 2025-01-02 19:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_rename_days_generatedcode_token_value_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='generatedcode',
            old_name='code',
            new_name='token',
        ),
    ]
