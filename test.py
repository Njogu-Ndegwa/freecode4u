# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class User(AbstractUser):
    USER_TYPES = (
        ('SUPER_ADMIN', 'Super Admin'),
        ('DISTRIBUTOR', 'Distributor'),
        ('AGENT', 'Agent')
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    distributor = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='agents')
    permissions = models.JSONField(default=dict)

class Manufacturer(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

class Fleet(models.Model):
    name = models.CharField(max_length=100)
    distributor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fleets')
    description = models.TextField(blank=True)

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    assigned_agent = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='customers')
    created_at = models.DateTimeField(auto_now_add=True)

class PaymentPlan(models.Model):
    name = models.CharField(max_length=100)
    distributor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_plans')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    days = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Item(models.Model):
    serial_number = models.CharField(max_length=100, unique=True)
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE, related_name='items')
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name='items')
    manufacturers = models.ManyToManyField(Manufacturer, related_name='items')
    assigned_agent = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_items')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def distributor(self):
        return self.fleet.distributor

class ItemPaymentPlan(models.Model):
    """Junction model to track which items are assigned to which payment plans"""
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='payment_plan_assignments')
    payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE, related_name='item_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['item', 'payment_plan', 'is_active']

    def save(self, *args, **kwargs):
        # Ensure the payment plan belongs to the item's distributor
        if self.payment_plan.distributor != self.item.distributor:
            raise ValidationError("Payment plan must belong to the item's distributor")
        super().save(*args, **kwargs)

class PaymentMessage(models.Model):
    phone_number = models.CharField(max_length=20)
    message_content = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class GeneratedCode(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='generated_codes')
    code = models.CharField(max_length=100)
    days = models.IntegerField()
    payment_message = models.ForeignKey(PaymentMessage, on_delete=models.CASCADE, related_name='generated_codes')
    created_at = models.DateTimeField(auto_now_add=True)

# serializers.py
class ItemPaymentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPaymentPlan
        fields = ['id', 'item', 'payment_plan', 'assigned_at', 'assigned_by', 'is_active']

class ItemSerializer(serializers.ModelSerializer):
    active_payment_plans = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ['id', 'serial_number', 'fleet', 'customer', 'manufacturers',
                 'assigned_agent', 'active_payment_plans', 'created_at']

    def get_active_payment_plans(self, obj):
        active_assignments = obj.payment_plan_assignments.filter(is_active=True)
        return PaymentPlanSerializer(
            [assignment.payment_plan for assignment in active_assignments],
            many=True
        ).data

# views.py
class ItemViewSet(viewsets.ModelViewSet):
    serializer_class = ItemSerializer
    permission_classes = [IsAssignedAgentOrHigher]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'SUPER_ADMIN':
            return Item.objects.all()
        elif user.user_type == 'DISTRIBUTOR':
            return Item.objects.filter(fleet__distributor=user)
        return Item.objects.filter(assigned_agent=user)

    @action(detail=True, methods=['post'])
    def assign_payment_plan(self, request, pk=None):
        item = self.get_object()
        payment_plan_id = request.data.get('payment_plan_id')
        
        try:
            payment_plan = PaymentPlan.objects.get(id=payment_plan_id)
            
            # Validate that the payment plan belongs to the distributor
            if payment_plan.distributor != item.distributor:
                return Response(
                    {'error': 'Payment plan must belong to the item\'s distributor'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Deactivate any existing active payment plan assignments
            ItemPaymentPlan.objects.filter(
                item=item,
                is_active=True
            ).update(is_active=False)
            
            # Create new payment plan assignment
            assignment = ItemPaymentPlan.objects.create(
                item=item,
                payment_plan=payment_plan,
                assigned_by=request.user
            )
            
            return Response(ItemPaymentPlanSerializer(assignment).data)
            
        except PaymentPlan.DoesNotExist:
            return Response(
                {'error': 'Payment plan not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def bulk_assign_payment_plan(self, request):
        payment_plan_id = request.data.get('payment_plan_id')
        item_ids = request.data.get('item_ids', [])
        
        try:
            payment_plan = PaymentPlan.objects.get(id=payment_plan_id)
            items = Item.objects.filter(id__in=item_ids)
            
            assignments = []
            for item in items:
                if payment_plan.distributor != item.distributor:
                    continue
                    
                # Deactivate existing assignments
                ItemPaymentPlan.objects.filter(
                    item=item,
                    is_active=True
                ).update(is_active=False)
                
                # Create new assignment
                assignment = ItemPaymentPlan.objects.create(
                    item=item,
                    payment_plan=payment_plan,
                    assigned_by=request.user
                )
                assignments.append(assignment)
            
            return Response(
                ItemPaymentPlanSerializer(assignments, many=True).data
            )
            
        except PaymentPlan.DoesNotExist:
            return Response(
                {'error': 'Payment plan not found'},
                status=status.HTTP_404_NOT_FOUND
            )