# urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Get all GeneratedCodes for an Item
    path('payments/make_payment/', views.make_payment_view, name='make-payment-view'),
    path('items/<int:item_id>/generated_codes/', views.get_generated_codes_for_item, name='get-generated-codes-for-item'),
    path('items/<int:item_id>/payments/', views.get_payments_for_item, name='get-payments-for-item'),
    path('item/generate_token/', views.generate_token_view, name='get-payments-for-item'),
    path('distributors/<int:distributor_id>/payments/', views.get_payments_for_distributor, name='get-payments-for-distributor'),
    path('payment_plans/', views.get_all_payment_plans, name='get-all-payment-plans'),
    path('items/assign_payment_plan/', views.assign_payment_plan_to_item, name='assign-payment-plan-to-item'),
    path('payment_plans/create/', views.create_payment_plan, name='create-payment-plan'),
]
