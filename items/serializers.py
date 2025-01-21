# serializers.py
from rest_framework import serializers
from .models import Manufacturer, Fleet, Item, EncoderState
from users.serializers import UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ['id', 'name', 'description', 'distributor', 'created_at', 'updated_at']
        read_only_fields = ['distributor']  # ensure the user can't override


class FleetSerializer(serializers.ModelSerializer):
    assigned_agent_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type='AGENT'),
        source='assigned_agent',  # Maps to model field
        write_only=True
    )
    assigned_agent = UserSerializer(read_only=True)
    class Meta:
        model = Fleet
        fields = [
            'id', 'name', 'distributor', 
            'assigned_agent', 'assigned_agent_id', 
            'description', 'created_at', 'updated_at']
        read_only_fields = ['distributor', 'assigned_agent']


class EncoderStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EncoderState
        fields = ['token_type', 'token_value', 'secret_key', 'starting_code', 'max_count', 'token', 'created_at', 'updated_at']

class ItemSerializer(serializers.ModelSerializer):
    encoder_state = EncoderStateSerializer(required=False)
    manufacturers = serializers.PrimaryKeyRelatedField(
        queryset=Manufacturer.objects.all(),
        required=False
    )

    class Meta:
        model = Item
        fields = [
            'id',
            'serial_number', 
            'manufacturers', 
            'encoder_state',
            'status',
            'payment_plan',
            'created_at', 
            'updated_at'
            ]
    
    def create(self, validated_data):
        encoder_state_data = validated_data.pop('encoder_state', None)
        manufacturers = validated_data.pop('manufacturers', None)
        fleet = self.context.get('fleet')  # Get fleet from context if needed

        # Create the item
        item = Item.objects.create(fleet=fleet, **validated_data)

        # Set the manufacturers
        if manufacturers:
            item.manufacturers = manufacturers
            item.save()

        # Create encoder state if provided
        if encoder_state_data:
            EncoderState.objects.create(item=item, **encoder_state_data)

        return item