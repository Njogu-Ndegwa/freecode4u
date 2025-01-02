# models.py
from django.db import models
from django.contrib.auth import get_user_model
from clients.models import Customer
from decimal import Decimal
User = get_user_model()

class Manufacturer(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    distributor = models.ForeignKey(
        User,
        null=False,    # or True if you want to allow None
        blank=False,
        on_delete=models.CASCADE,
        related_name='manufacturers'
    )

    def __str__(self):
        return f"{self.name} (owned by {self.distributor.username})"
    

class Fleet(models.Model):
    name = models.CharField(max_length=100, unique=True)
    distributor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fleets'
    )
    assigned_agent = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_fleets'
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} (Distributor: {self.distributor}, Agent: {self.assigned_agent})"

class EncoderState(models.Model):
    item = models.OneToOneField(
        'Item',
        on_delete=models.CASCADE,
        related_name='encoder_state'
    )
    token_type = models.CharField(max_length=100)
    token_value = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)
    starting_code = models.CharField(max_length=100)
    max_count = models.IntegerField()
    token = models.CharField(max_length=255)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Encoder State for Item {self.item.serial_number}"
    
    
class Item(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partially_paid', 'Partially Paid'),
        ('fully_paid', 'Fully Paid'),
    ]
    serial_number = models.CharField(max_length=100, unique=True)
    fleet = models.ForeignKey(
        Fleet, 
        on_delete=models.CASCADE, 
        related_name='items',
        null=True,
        blank=True,
    )
    customer = models.ForeignKey(
        'clients.Customer',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='items'
    )
    manufacturers = models.ForeignKey(
        Manufacturer,
        related_name='items',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_plan = models.ForeignKey(
        'payments.PaymentPlan',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='item_payment_plan'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Item {self.serial_number}"
    
    def calculate_total_paid(self):
        return self.payments.aggregate(total_paid=models.Sum('amount_paid'))['total_paid'] or Decimal('0.00')

    def update_status(self):
        total_paid = self.calculate_total_paid()
        if self.payment_plan:
            if total_paid >= self.payment_plan.total_amount:
                self.status = 'fully_paid'
            elif total_paid > 0:
                self.status = 'partially_paid'
            else:
                self.status = 'pending'
            self.save()