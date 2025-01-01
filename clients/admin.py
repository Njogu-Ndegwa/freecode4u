# admin.py
from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """
    Custom admin for the Customer model.
    """
    # Choose which columns are displayed in the listing
    list_display = ['name', 'email', 'phone_number', 'distributor', 'assigned_agent', 'created_at']
    
    # Add search functionality (optional)
    search_fields = ['name', 'email', 'phone_number']
    
    # Optionally add list filters (e.g., by distributor or agent)
    list_filter = ['distributor', 'assigned_agent']
