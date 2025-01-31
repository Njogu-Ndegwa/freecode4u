# serializers.py
from rest_framework import serializers
from .models import Customer
from users.serializers import UserSerializer
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone_number', 'assigned_agent', 'distributor', 'created_at']
        read_only_fields = ['distributor']  # ensure the user can't override distributor
