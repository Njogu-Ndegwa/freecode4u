# serializers.py
from rest_framework import serializers
from .models import Manufacturer, Fleet, Item, EncoderState

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


class EncoderStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EncoderState
        fields = ['token_type', 'token_value', 'secret_key', 'starting_code', 'max_count', 'token']

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
            'created_at'
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