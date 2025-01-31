from django.urls import path
from . import views

urlpatterns = [
    # Manufacturers
    path('manufacturers/', views.manufacturer_list_create_view, name='manufacturer-list-create'),
    path('manufacturers/<int:pk>/', views.manufacturer_detail_view, name='manufacturer-detail'),


    # Fleets
    path('fleets/', views.fleet_list_create_view, name='fleet-list-create'),
    path('fleets/<int:pk>/', views.fleet_detail_view, name='fleet-detail'),
    path('fleets/assign/', views.assign_fleets_view, name='fleet-assign-agent'),
    path('fleets/reassign/', views.reassign_fleets_view, name='fleet-reassign-agent'),

    # Items
    path('items/', views.items_view, name='items-item'),
    path('items/<int:pk>/', views.item_detail_view, name='item-detail'),
    path('items/bulk_create/', views.create_items_bulk_view, name='create-items-bulk'),
    path('items/assign_fleet/', views.assign_item_to_fleet_view, name='assign-item-fleet'),
    path('items/reassign_fleet/', views.reassign_item_to_fleet_view, name='reassign-item-fleet'),
    path('fleets/<int:fleet_id>/items/', views.get_items_in_fleet_view, name='fleet-items'),
    path('items/assign_customer/', views.assign_customer_item_view, name='assign-customer-item-view'),
]
