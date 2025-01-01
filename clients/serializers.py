# serializers.py
from rest_framework import serializers
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        # or list them explicitly:
        # fields = ['id', 'name', 'email', 'phone_number', 'assigned_agent', 'distributor', 'created_at']
        read_only_fields = ['distributor']  # ensure the user can't override distributor
