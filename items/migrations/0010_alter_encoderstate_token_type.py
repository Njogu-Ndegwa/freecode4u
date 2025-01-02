# Generated by Django 5.1.4 on 2025-01-02 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0009_encoderstate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='encoderstate',
            name='token_type',
            field=models.CharField(choices=[('ADD_TIME', 'ADD_TIME'), ('SET_TIME', 'SET_TIME'), ('DISABLE_PAYG', 'DISABLE_PAYG'), ('COUNTER_SYNC', 'COUNTER_SYNC')], max_length=100),
        ),
    ]
