from django.urls import path
from . import views

urlpatterns = [
    path('customers/', views.customer_list_create_view, name='customer-list-create'),
    path('customers/<int:pk>/', views.customer_detail_view, name='customer-detail'),
    path('customers/assign_agent/', views.assign_multiple_customers_view, name='assing-multiple-customers-view'),
    path('customers/reassign_agent/', views.reassign_multiple_customers_view, name='reassign-multiple-customers-view'),
    path('mac_address/', views.mac_address_view, name='reassign_multiple_customers_view')
]   
