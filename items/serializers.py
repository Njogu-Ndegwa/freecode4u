# serializers.py
from rest_framework import serializers
from .models import Manufacturer, Fleet, Item

class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ['id', 'name', 'description', 'distributor']
        read_only_fields = ['distributor']  # ensure the user can't override


class FleetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fleet
        fields = ['id', 'name', 'distributor', 'assigned_agent', 'description']
        read_only_fields = ['distributor', 'assigned_agent']


class ItemSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating/reading Item objects.
    We'll treat 'fleet' as read-only from a normal create endpoint,
    since we have separate logic for assignment. 
    But you can allow or disallow as you wish.
    """
    class Meta:
        model = Item
        fields = [
            'id', 
            'serial_number', 
            'fleet', 
            'customer', 
            'manufacturers',
            'balance', 
            'created_at'
        ]
        read_only_fields = ['fleet', 'customer', 'created_at', 'balance']