

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


class ItemPaymentPlan(models.Model):
    """Junction model to track which items are assigned to which payment plans"""
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='payment_plan_assignments')
    payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE, related_name='item_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['item', 'payment_plan', 'is_active']


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