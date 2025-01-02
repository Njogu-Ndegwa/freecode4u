# payments/admin.py

from django.contrib import admin
from .models import PaymentPlan, Payment, GeneratedCode, PaymentMessage

@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    """
    Admin interface for PaymentPlan model.
    """
    list_display = ('name', 'distributor_username', 'total_amount', 'interval_type', 'interval_amount', 'created_at')
    search_fields = ('name', 'distributor__username')
    list_filter = ('distributor', 'interval_type')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    def distributor_username(self, obj):
        """
        Displays the username of the distributor.
        """
        return obj.distributor.username if obj.distributor else "No Distributor"
    distributor_username.short_description = 'Distributor Username'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin interface for Payment model.
    """
    list_display = ('id', 'item_serial_number', 'payment_plan_name', 'amount_paid', 'paid_at', 'customer_name', 'note')
    search_fields = ('item__serial_number', 'payment_plan__name', 'customer__name')
    list_filter = ('payment_plan', 'customer', 'paid_at')
    readonly_fields = ('paid_at',)
    ordering = ('-paid_at',)

    def item_serial_number(self, obj):
        """
        Displays the serial number of the related item.
        """
        return obj.item.serial_number
    item_serial_number.short_description = 'Item Serial Number'

    def payment_plan_name(self, obj):
        """
        Displays the name of the related payment plan.
        """
        return obj.payment_plan.name if obj.payment_plan else "No Payment Plan"
    payment_plan_name.short_description = 'Payment Plan Name'

    def customer_name(self, obj):
        """
        Displays the name of the related customer.
        """
        return obj.customer.name if obj.customer else "No Customer"
    customer_name.short_description = 'Customer Name'

@admin.register(GeneratedCode)
class GeneratedCodeAdmin(admin.ModelAdmin):
    """
    Admin interface for GeneratedCode model.
    """
    list_display = ('token', 'item_serial_number', 'token_value', 'payment_message_excerpt', 'created_at')
    search_fields = ('token', 'item__serial_number', 'payment_message__message')
    list_filter = ('payment_message', 'token_value', 'created_at')
    readonly_fields = ('token', 'created_at')
    ordering = ('-created_at',)

    def item_serial_number(self, obj):
        """
        Displays the serial number of the related item.
        """
        return obj.item.serial_number
    item_serial_number.short_description = 'Item Serial Number'

    def payment_message_excerpt(self, obj):
        """
        Displays an excerpt of the payment message.
        """
        return (obj.payment_message.message[:75] + '...') if obj.payment_message and len(obj.payment_message.message) > 75 else obj.payment_message.message
    payment_message_excerpt.short_description = 'Payment Message'

@admin.register(PaymentMessage)
class PaymentMessageAdmin(admin.ModelAdmin):
    """
    Admin interface for PaymentMessage model.
    """
    list_display = ('id', 'message_excerpt')
    search_fields = ('message',)
    list_filter = ()
    ordering = ('id',)

    def message_excerpt(self, obj):
        """
        Displays an excerpt of the message.
        """
        return (obj.message[:75] + '...') if len(obj.message) > 75 else obj.message
    message_excerpt.short_description = 'Message Excerpt'
