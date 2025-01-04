# serializers.py

from rest_framework import serializers
from .models import GeneratedCode, Payment, PaymentPlan
from items.models import Item 

class GeneratedCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedCode
        fields = ['id', 'item', 'token', 'token_value', 'token_type', 'max_count', 'payment_message', 'created_at', 'updated_at']
        read_only_fields = ['id', 'token', 'token_value', 'token_type', 'max_count', 'payment_message', 'created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    payment_plan = serializers.StringRelatedField()  # Displays the payment plan name
    customer = serializers.StringRelatedField()      # Displays the customer name
    item = serializers.StringRelatedField()          # Displays the item serial number

    class Meta:
        model = Payment
        fields = ['id', 'item', 'payment_plan', 'amount_paid', 'paid_at', 'customer', 'note']
        read_only_fields = ['id',  'distributor', 'paid_at']


class PaymentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentPlan
        fields = ['id', 'name', 'total_amount', 'interval_type', 'interval_amount', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# serializers.py

class AssignPaymentPlanSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    payment_plan_id = serializers.IntegerField()

    def validate_item_id(self, value):
        if not Item.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Item does not exist.")
        return value

    def validate_payment_plan_id(self, value):
        if not PaymentPlan.objects.filter(pk=value).exists():
            raise serializers.ValidationError("PaymentPlan does not exist.")
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        payment_plan = PaymentPlan.objects.get(pk=attrs['payment_plan_id'])
        if payment_plan.distributor != user and user.user_type != 'SUPER_ADMIN':
            raise serializers.ValidationError("You can only assign your own PaymentPlans.")
        return attrs

    

# serializers.py

class CreatePaymentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentPlan
        fields = ['id', 'name', 'total_amount', 'interval_type', 'interval_amount', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_interval_type(self, value):
        allowed_types = [choice[0] for choice in PaymentPlan.INTERVAL_TYPES]
        if value.lower() not in allowed_types:
            raise serializers.ValidationError(f"interval_type must be one of {allowed_types}.")
        return value.lower()

    def create(self, validated_data):
        user = self.context['request'].user
        return PaymentPlan.objects.create(distributor=user, **validated_data)

