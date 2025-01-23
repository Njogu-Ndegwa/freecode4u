# serializers.py
from rest_framework import serializers
from .models import Manufacturer, Fleet, Item, EncoderState
from users.serializers import UserSerializer
from django.contrib.auth import get_user_model
from clients.serializers import CustomerSerializer
from payments.serializers import PaymentPlanSerializer


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
    fleet = serializers.PrimaryKeyRelatedField(
        queryset=Fleet.objects.all(),
        required=True,
        write_only=True  # Optional: prevents showing PK in output
    )

    class Meta:
        model = Item
        fields = [
            'id',
            'serial_number', 
            'manufacturers', 
            'encoder_state',
            'fleet',
            'payment_plan',
            'customer',
            'status',
            'payment_plan',
            'created_at', 
            'updated_at'
            ]
    
    def validate_fleet(self, value):
        """Ensure the user owns the fleet if provided"""
        user = self.context['request'].user
        if value and value.distributor != user:
            raise serializers.ValidationError("You don't own this fleet.")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Replace primary keys with nested representations
        data['manufacturers'] = ManufacturerSerializer(instance.manufacturers).data if instance.manufacturers else None
        data['customer'] = CustomerSerializer(instance.customer).data if instance.customer else None
        data['payment_plan'] = PaymentPlanSerializer(instance.payment_plan).data if instance.payment_plan else None
        data['fleet'] = FleetSerializer(instance.fleet).data if instance.fleet else None

        return data
    
    def create(self, validated_data):
        """Handle nested creation and automatic distributor assignment"""
        encoder_state_data = validated_data.pop('encoder_state', None)
        manufacturers = validated_data.pop('manufacturers', None)
        
        item = Item.objects.create(**validated_data)

        if manufacturers:
            item.manufacturers = manufacturers
            item.save()

        if encoder_state_data:
            EncoderState.objects.create(item=item, **encoder_state_data)

        return item

    def update(self, instance, validated_data):
        # Handle nested encoder_state
        encoder_state_data = validated_data.pop('encoder_state', None)
        
        # Update main fields
        instance = super().update(instance, validated_data)

        # Update or create encoder state
        if encoder_state_data is not None:
            if instance.encoder_state:
                # Update existing encoder state
                encoder_state_serializer = EncoderStateSerializer(
                    instance.encoder_state, 
                    data=encoder_state_data,
                    partial=self.partial
                )
                encoder_state_serializer.is_valid(raise_exception=True)
                encoder_state_serializer.save()
            else:
                # Create new encoder state
                EncoderState.objects.create(item=instance, **encoder_state_data)

        return instance