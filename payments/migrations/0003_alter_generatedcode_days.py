# Generated by Django 5.1.4 on 2025-01-02 06:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_alter_paymentplan_options_paymentplan_distributor_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generatedcode',
            name='days',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
