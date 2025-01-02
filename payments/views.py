# views_payments.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django.db import transaction
import uuid  # For generating unique codes

from .models import ( PaymentPlan, Payment, 
    GeneratedCode, PaymentMessage, 
)

from .serializers import GeneratedCodeSerializer, PaymentPlanSerializer, AssignPaymentPlanSerializer, CreatePaymentPlanSerializer
from items.models import Item
from django.contrib.auth import get_user_model
from .serializers import PaymentSerializer

User = get_user_model()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def make_payment_view(request):
    """
    POST /payments/make_payment/
    {
      "item_id": <int>,
      "amount": <decimal>,
      "note": "optional note"  // Optional
    }

    Workflow:
    1) Authenticate and authorize the user.
    2) Validate the input data.
    3) Retrieve the item and ensure ownership.
    4) Determine the PaymentPlan associated with the Item.
    5) Create a Payment record.
    6) Credit the item's balance.
    7) If PaymentPlan exists:
       - If balance >= interval_amount:
           a) Debit the balance by interval_amount.
           b) Generate a unique code.
           c) Respond with the generated code and remaining balance.
       - Else:
           a) Retain the balance.
           b) Respond indicating insufficient balance.
    8) If no PaymentPlan exists:
       - Respond indicating payment was recorded without triggering any plan logic.
    """

    user = request.user

    # 1) Authenticate and authorize
    if user.user_type not in ['DISTRIBUTOR', 'SUPER_ADMIN']:
        raise PermissionDenied("You do not have permission to make payments.")

    # 2) Validate input data
    item_id = request.data.get('item_id')
    amount_str = request.data.get('amount')
    if not item_id:
        return Response({"detail": "item_id is required."}, status=status.HTTP_400_BAD_REQUEST)
    if not amount_str:
        return Response({"detail": "amount is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        amount = Decimal(amount_str)
        if amount <= 0:
            return Response({"detail": "amount must be a positive number."}, status=status.HTTP_400_BAD_REQUEST)
    except:
        return Response({"detail": "Invalid amount format."}, status=status.HTTP_400_BAD_REQUEST)

    note = request.data.get('note', '')

    # 3) Retrieve and validate the item
    item = get_object_or_404(Item, pk=item_id)

    if user.user_type == 'DISTRIBUTOR' and item.fleet.distributor != user:
        raise PermissionDenied("You do not own this item (through its fleet).")

    # Infer customer from item
    customer = item.customer  # Assuming item.customer is already set

    # 4) Determine PaymentPlan associated with the Item
    payment_plan = item.payment_plan  # Directly access via OneToOneField
    
     # Calculate total paid so far
    total_paid = item.calculate_total_paid()
    will_complete_payment = (total_paid + amount) >= payment_plan.total_amount
    # 5) Process payment within a transaction for atomicity

    is_fully_paid = False
    if payment_plan and total_paid >= payment_plan.total_amount:
        is_fully_paid = True

    try:
        with transaction.atomic():
            # 5.1) Create the Payment record, associating with the PaymentPlan if it exists
            payment = Payment.objects.create(
                item=item,
                payment_plan=payment_plan,  # Associate with PaymentPlan if exists
                amount_paid=amount,
                customer=customer,
                note=note
            )

            # 5.2) Credit the item's balance
            item.balance += amount
            item.save()
            
            # 6) Apply PaymentPlan logic if PaymentPlan exists
            if payment_plan:
                if is_fully_paid:
                    # 6.1) For fully paid items, just record the payment and balance
                    return Response({
                        "detail": "Payment recorded for fully paid item. No code generated.",
                        "current_balance": str(item.balance),
                        "status": item.status
                    }, status=status.HTTP_200_OK)
                interval_amount = payment_plan.interval_amount
                if will_complete_payment:
                    # Generate a special completion code
                    completion_code = str(uuid.uuid4()).replace('-', '').upper()[:12]
                    
                    payment_message, _ = PaymentMessage.objects.get_or_create(
                        defaults={'message': "Congratulations! Full payment completed."}
                    )

                    # Create a special completion code
                    completion_generated_code = GeneratedCode.objects.create(
                        item=item,
                        code=completion_code,
                        days=None,  # or specify a special value for completion codes
                        payment_message=payment_message
                    )

                    # Update status after generating completion code
                    item.update_status()

                    # Return early with completion code
                    return Response({
                        "detail": "Congratulations! Item fully paid.",
                        "completion_code": completion_generated_code.code,
                        "remaining_balance": str(item.balance),
                        "status": item.status,
                        "is_completion": True
                    }, status=status.HTTP_200_OK)
                if item.balance >= interval_amount:
                    # 6.1) Debit the balance by interval_amount
                    num_intervals = int(item.balance // interval_amount)
                    total_debit = interval_amount * num_intervals
                    
                    # 6.2) Debit the balance by the total amount
                    item.balance -= total_debit
                    item.save()

                    # 6.2) Generate a unique code
                    code = str(uuid.uuid4()).replace('-', '').upper()[:12]  # 12-character code

                    # 6.3) Determine the number of days based on interval_type
                    interval_type_to_days = {
                        'hourly': 1 / 24,  # Fractional days, e.g., 1 hour = 1/24 day
                        'daily': 1,
                        'weekly': 7,
                        'monthly': 30,  # Approximate; adjust as needed
                        # Add more mappings if necessary
                    }
                    days = interval_type_to_days.get(payment_plan.interval_type.lower(), 1)
                    
                    total_days = days * num_intervals
                    # 6.4) Create or retrieve a PaymentMessage
                    payment_message, created = PaymentMessage.objects.get_or_create(
                        # Define your criteria for getting/creating a PaymentMessage
                        # Example: based on PaymentPlan or other attributes
                        defaults={'message': f"Code generated for {payment_plan.interval_type} usage."}
                    )

                    # 6.5) Create a GeneratedCode record
                    generated_code = GeneratedCode.objects.create(
                        item=item,
                        code=code,
                        days=total_days,
                        payment_message=payment_message
                    )

                    # 6.6) Optionally, perform external API call here
                    # e.g., send_code_to_customer(generated_code)

                    # 6.7) Respond with the generated code and remaining balance
                    return Response({
                        "detail": "Payment successful, code generated.",
                        "code": generated_code.code,
                        "days": generated_code.days,
                        "remaining_balance": str(item.balance)
                    }, status=status.HTTP_200_OK)
                else:
                    # 6.8) Not enough balance to cover the interval amount
                    return Response({
                        "detail": "Payment added to item balance but not enough to cover plan cost. No code generated.",
                        "current_balance": str(item.balance)
                    }, status=status.HTTP_200_OK)
            else:
                # 7) No PaymentPlan exists
                return Response({
                    "detail": "Payment successful, but no PaymentPlan to apply."
                }, status=status.HTTP_200_OK)

    except Exception as e:
        # Handle unexpected errors
        return Response({
            "detail": "An error occurred while processing the payment.",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_generated_codes_for_item(request, item_id):
    """
    Retrieve all GeneratedCodes related to a specific Item.
    """
    item = get_object_or_404(Item, pk=item_id)

    # Permission Check: Only SUPER_ADMIN or Distributor owning the Item can view codes
    user = request.user
    if user.user_type == 'DISTRIBUTOR' and item.fleet.distributor != user:
        return Response({"detail": "You do not have permission to view codes for this item."}, status=status.HTTP_403_FORBIDDEN)

    codes = GeneratedCode.objects.filter(item=item)
    serializer = GeneratedCodeSerializer(codes, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payments_for_item(request, item_id):
    """
    Retrieve all Payments related to a specific Item.
    """
    item = get_object_or_404(Item, pk=item_id)

    # Permission Check: Only SUPER_ADMIN or Distributor owning the Item can view payments
    user = request.user
    if user.user_type == 'DISTRIBUTOR' and item.fleet.distributor != user:
        return Response({"detail": "You do not have permission to view payments for this item."}, status=status.HTTP_403_FORBIDDEN)

    payments = Payment.objects.filter(item=item).order_by('-paid_at')
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payments_for_distributor(request, distributor_id):
    """
    Retrieve all Payments related to a specific Distributor.
    """
    distributor = get_object_or_404(User, pk=distributor_id, user_type='DISTRIBUTOR')

    # Permission Check: Only SUPER_ADMIN or the Distributor themselves can view their payments
    user = request.user
    if user.user_type != 'SUPER_ADMIN' and user != distributor:
        return Response({"detail": "You do not have permission to view payments for this distributor."}, status=status.HTTP_403_FORBIDDEN)

    payments = Payment.objects.filter(item__fleet__distributor=distributor).order_by('-paid_at')
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# views.py

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_payment_plans(request):
    """
    Retrieve all PaymentPlans.
    - SUPER_ADMIN: sees all PaymentPlans.
    - DISTRIBUTOR: sees only their own PaymentPlans.
    """
    user = request.user
    if user.user_type == 'SUPER_ADMIN':
        payment_plans = PaymentPlan.objects.all().order_by('-created_at')
    elif user.user_type == 'DISTRIBUTOR' or user.user_type == 'AGENT':
        payment_plans = PaymentPlan.objects.filter(distributor=user).order_by('-created_at')
    else:
        return Response({"detail": "You do not have permission to view payment plans."}, status=status.HTTP_403_FORBIDDEN)

    serializer = PaymentPlanSerializer(payment_plans, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_payment_plan_to_item(request):
    """
    Assign a PaymentPlan to an Item.
    """
    serializer = AssignPaymentPlanSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    item_id = serializer.validated_data['item_id']
    payment_plan_id = serializer.validated_data['payment_plan_id']

    item = get_object_or_404(Item, pk=item_id)
    payment_plan = get_object_or_404(PaymentPlan, pk=payment_plan_id)

    # Permission Check: Only SUPER_ADMIN or Distributor owning the Item can assign a payment plan
    user = request.user
    if user.user_type == 'DISTRIBUTOR' and item.fleet.distributor != user:
        return Response({"detail": "You do not have permission to assign a payment plan to this item."}, status=status.HTTP_403_FORBIDDEN)

    # Assign the PaymentPlan to the Item
    item.payment_plan = payment_plan
    item.save()

    return Response({
        "detail": f"PaymentPlan '{payment_plan.name}' has been assigned to Item '{item.serial_number}'."
    }, status=status.HTTP_200_OK)


# views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_plan(request):
    """
    Create a new PaymentPlan.
    - SUPER_ADMIN: can create payment plans for any distributor (if needed).
    - DISTRIBUTOR: can create their own PaymentPlans.
    """
    user = request.user

    # Only SUPER_ADMIN and DISTRIBUTOR can create PaymentPlans
    if user.user_type not in ['SUPER_ADMIN', 'DISTRIBUTOR']:
        return Response({"detail": "You do not have permission to create payment plans."}, status=status.HTTP_403_FORBIDDEN)

    serializer = CreatePaymentPlanSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    payment_plan = serializer.save()
    return Response({
        "detail": f"PaymentPlan '{payment_plan.name}' has been created successfully.",
        "payment_plan": PaymentPlanSerializer(payment_plan).data
    }, status=status.HTTP_201_CREATED)
