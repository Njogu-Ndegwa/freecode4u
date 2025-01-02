
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class PaymentPlan(models.Model):
    INTERVAL_TYPES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        # Add more as needed
    ]

    distributor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payment_plans',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interval_type = models.CharField(max_length=50, choices=INTERVAL_TYPES)
    interval_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('distributor', 'name')  # Ensures unique names per distributor
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.interval_type}) by {self.distributor.username}"



class Payment(models.Model):
    item = models.ForeignKey(
        'items.Item', 
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_plan = models.ForeignKey(
        PaymentPlan,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='payments'
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(
        'clients.Customer', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='payments'
    )
    note = models.TextField(blank=True)

    def __str__(self):
        return (f"Payment of {self.amount_paid} on item {self.item.serial_number} "
                f"{'with plan ' + self.payment_plan.name if self.payment_plan else ''}")


class GeneratedCode(models.Model):
    item = models.ForeignKey(
        'items.Item', 
        on_delete=models.CASCADE,
        related_name='generated_codes'
    )
    code = models.CharField(max_length=20, unique=True)
    days = models.IntegerField(null=True, blank=True)
    payment_message = models.ForeignKey(
        'PaymentMessage',
        on_delete=models.CASCADE,
        related_name='generated_codes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Code {self.code} for Item {self.item.serial_number}"

class PaymentMessage(models.Model):
    message = models.TextField()

    def __str__(self):
        return self.message