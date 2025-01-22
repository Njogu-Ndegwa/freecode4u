# admin.py
from django.contrib import admin
from .models import Manufacturer, Fleet, EncoderState, Item
from django.utils import timezone


class SoftDeleteAdmin(admin.ModelAdmin):
    """Admin configuration for soft-delete models"""
    list_display = ('__str__', 'deleted_status', 'deleted_at')
    list_filter = ('deleted_status',)
    actions = ['soft_delete_selected']

    def get_queryset(self, request):
        """Show all items including soft-deleted"""
        return self.model.all_objects.all()

    def soft_delete_selected(self, request, queryset):
        """Custom admin action for soft deletion"""
        queryset.update(deleted_status=True, deleted_at=timezone.now())
        self.message_user(request, f"Soft deleted {queryset.count()} items")
    soft_delete_selected.short_description = "Soft delete selected items"

    def delete_queryset(self, request, queryset):
        """Override bulk delete to use soft delete"""
        queryset.update(deleted_status=True, deleted_at=timezone.now())

    def delete_model(self, request, obj):
        """Override single object delete to use soft delete"""
        obj.deleted_status = True
        obj.deleted_at = timezone.now()
        obj.save()

# Remove the default delete action
admin.site.disable_action('delete_selected')

@admin.register(Manufacturer)
class ManufacturerAdmin(SoftDeleteAdmin):
    list_display = ('id', 'name', 'distributor', 'created_at', 'deleted_status', 'deleted_at')
    search_fields = ('name', 'distributor__username')

@admin.register(Fleet)
class FleetAdmin(SoftDeleteAdmin):
    list_display = ('id', 'name', 'distributor', 'assigned_agent', 'created_at', 'deleted_status', 'deleted_at')
    search_fields = ('name', 'distributor__username', 'assigned_agent__username')

@admin.register(EncoderState)
class EncoderStateAdmin(SoftDeleteAdmin):
    list_display = ('id', 'item', 'token_type', 'created_at')
    search_fields = ('item__serial_number',)

@admin.register(Item)
class ItemAdmin(SoftDeleteAdmin):
    list_display = ('id', 'serial_number', 'fleet', 'customer', 'status', 'deleted_status', 'deleted_at')
    list_filter = ('status', 'deleted_status')
    search_fields = ('serial_number', 'fleet__name')