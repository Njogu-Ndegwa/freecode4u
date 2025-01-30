# views_payments.py
import requests
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
from items.models import Item, EncoderState
from django.contrib.auth import get_user_model
from .serializers import PaymentSerializer

User = get_user_model()

def validate_input_data(request):
    """Validate input data from the request."""
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
        return item_id, amount
    except:
        return Response({"detail": "Invalid amount format."}, status=status.HTTP_400_BAD_REQUEST)

def authorize_user(user, item):
    """Authorize the user to make payments for the item."""
    if user.user_type == 'DISTRIBUTOR' and item.fleet.distributor != user:
        raise PermissionDenied("You do not own this item (through its fleet).")

def create_payment_record(item, payment_plan, amount, customer, note):
    """Create a Payment record."""
    return Payment.objects.create(
        item=item,
        payment_plan=payment_plan,
        amount_paid=amount,
        customer=customer,
        note=note
    )

def call_external_api(encoder_state, token_type, token_value):
    """Call the external API to generate a token."""
    api_url = "https://open-token.omnivoltaic.com/operate_token/"
    payload = {
        "token_type": token_type,
        "token_value": token_value,
        "max_count": encoder_state.max_count,
        "starting_code": encoder_state.starting_code,
        "secret_key": encoder_state.secret_key,
    }
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to generate token via external API: {e}")

def update_encoder_state(encoder_state, token_response):
    """Update the EncoderState with the new token and other data."""
    encoder_state.token = token_response.get("token")
    encoder_state.token_type = token_response.get("token_type")
    encoder_state.token_value = token_response.get("token_value")
    encoder_state.max_count = token_response.get("max_count")
    encoder_state.save()

def create_generated_code(item, token_response, payment_message):
    """Create a GeneratedCode record."""
    return GeneratedCode.objects.create(
        item=item,
        token=token_response.get("token"),
        token_value=token_response.get("token_value"),
        token_type=token_response.get("token_type"),
        max_count=token_response.get("max_count"),
        payment_message=payment_message
    )

def handle_payment_plan_logic(item, payment_plan, total_paid, amount):
    """Handle the logic for applying the PaymentPlan."""
    if total_paid >= payment_plan.total_amount:
        return Response({
            "detail": "Payment recorded for fully paid item. No code generated.",
            "current_balance": str(item.balance),
            "status": item.status
        }, status=status.HTTP_200_OK)

    interval_amount = payment_plan.interval_amount
    if (total_paid + amount) >= payment_plan.total_amount:
        return handle_completion_code(item, payment_plan)

    if item.balance >= interval_amount:
        return handle_interval_payment(item, payment_plan)

    return Response({
        "detail": "Payment added to item balance but not enough to cover plan cost. No code generated.",
        "current_balance": str(item.balance)
    }, status=status.HTTP_200_OK)

def handle_completion_code(item, payment_plan):
    """Handle the logic for generating a completion code."""
    encoder_state = EncoderState.objects.get(item=item)
    token_response = call_external_api(encoder_state, "DISABLE_PAYG", 1)
    update_encoder_state(encoder_state, token_response)

    payment_message, _ = PaymentMessage.objects.get_or_create(
        defaults={'message': "Congratulations! Full payment completed."}
    )
    create_generated_code(item, token_response, payment_message)

    item.update_status()

    return Response({
        "detail": "Congratulations! Item fully paid.",
        "completion_code": token_response.get("token"),
        "remaining_balance": str(item.balance),
        "status": item.status,
        "is_completion": True
    }, status=status.HTTP_200_OK)

def handle_interval_payment(item, payment_plan):
    """Handle the logic for generating a token for interval payments."""
    num_intervals = int(item.balance // payment_plan.interval_amount)
    total_debit = payment_plan.interval_amount * num_intervals
    item.balance -= total_debit
    item.save()

    interval_type_to_days = {
        'hourly': 1 / 24,
        'daily': 1,
        'weekly': 7,
        'monthly': 30,
    }
    days = interval_type_to_days.get(payment_plan.interval_type.lower(), 1)
    total_days = days * num_intervals

    encoder_state = EncoderState.objects.get(item=item)
    token_response = call_external_api(encoder_state, "ADD_TIME", total_days)
    update_encoder_state(encoder_state, token_response)

    payment_message, _ = PaymentMessage.objects.get_or_create(
        defaults={'message': f"Code generated for {payment_plan.interval_type} usage."}
    )
    generated_code = create_generated_code(item, token_response, payment_message)

    return Response({
        "detail": "Payment successful, token generated via external API.",
        "token": generated_code.token,
        "days": generated_code.token_value,
        "remaining_balance": str(item.balance)
    }, status=status.HTTP_200_OK)

# Main view
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
    """
    user = request.user

    # 1) Authenticate and authorize
    if user.user_type not in ['DISTRIBUTOR', 'SUPER_ADMIN']:
        raise PermissionDenied("You do not have permission to make payments.")

    # 2) Validate input data
    validation_result = validate_input_data(request)
    if isinstance(validation_result, Response):
        return validation_result
    item_id, amount = validation_result

    note = request.data.get('note', '')

    # 3) Retrieve and validate the item
    item = get_object_or_404(Item, pk=item_id)
    authorize_user(user, item)

    # Infer customer from item
    customer = item.customer

    # 4) Determine PaymentPlan associated with the Item
    payment_plan = item.payment_plan

    # Calculate total paid so far
    total_paid = item.calculate_total_paid()

    try:
        with transaction.atomic():
            # 5) Create the Payment record and credit the item's balance
            create_payment_record(item, payment_plan, amount, customer, note)
            item.balance += amount
            item.save()

            # 6) Apply PaymentPlan logic if PaymentPlan exists
            if payment_plan:
                return handle_payment_plan_logic(item, payment_plan, total_paid, amount)
            else:
                return Response({
                    "detail": "Payment successful, but no PaymentPlan to apply."
                }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "detail": "An error occurred while processing the payment.",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_token_view(request):
    """
    POST /payments/generate_token/
    {
      "item_id": <int>,
      "token_type": "ADD_TIME" | "DISABLE_PAYG" | "SET_TIME" | "COUNTER_SYNC",
      "token_value": <int>,  # Number of days for ADD_TIME, 1 for DISABLE_PAYG
    }

    Workflow:
    1) Authenticate and authorize the user.
    2) Validate the input data.
    3) Retrieve the item and ensure ownership.
    4) Retrieve the EncoderState for the item.
    5) Call the external API to generate a token.
    6) Update the EncoderState with the new token.
    7) Create a GeneratedCode record for history.
    8) Respond with the generated token and details.
    """
    user = request.user

    # 1) Authenticate and authorize
    if user.user_type not in ['DISTRIBUTOR', 'SUPER_ADMIN']:
        raise PermissionDenied("You do not have permission to generate tokens.")

    # 2) Validate input data
    item_id = request.data.get('item_id')
    token_type = request.data.get('token_type')
    token_value = request.data.get('token_value')

    if not item_id:
        return Response({"detail": "item_id is required."}, status=status.HTTP_400_BAD_REQUEST)
    if not token_type or token_type not in ["ADD_TIME", "DISABLE_PAYG", "SET_TIME", "COUNTER_SYNC"]:
        return Response({"detail": "token_type must be either 'ADD_TIME' or 'DISABLE_PAYG' or SET_TIME or COUNTER_SYNC."}, status=status.HTTP_400_BAD_REQUEST)
    if not token_value or not isinstance(token_value, int) or token_value <= 0:
        return Response({"detail": "token_value must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

    # 3) Retrieve and validate the item
    item = get_object_or_404(Item, pk=item_id)
    if user.user_type == 'DISTRIBUTOR' and item.fleet.distributor != user:
        raise PermissionDenied("You do not own this item (through its fleet).")

    # 4) Retrieve the EncoderState for the item
    encoder_state = get_object_or_404(EncoderState, item=item)

    try:
        # 5) Call the external API to generate a token
        token_response = call_external_api(encoder_state, token_type, token_value)

        # 6) Update the EncoderState with the new token
        update_encoder_state(encoder_state, token_response)

        # 7) Create a GeneratedCode record for history
        payment_message, _ = PaymentMessage.objects.get_or_create(
            defaults={'message': f"Token generated for {token_type}."}
        )
        generated_code = create_generated_code(item, token_response, payment_message)

        # 8) Respond with the generated token and details
        return Response({
            "detail": "Token generated successfully.",
            "token": generated_code.token,
            "token_type": generated_code.token_type,
            "token_value": generated_code.token_value,
            "max_count": generated_code.max_count,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "detail": "An error occurred while generating the token.",
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

    {
    item_id: <int>
    payment_plan_id: <int>
    }
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
        "detail": "Item has been successfully assigned to a Payment Plan.",
        "item_id": item.id,
        "customer_id": payment_plan.id
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


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def payment_plan_detail_view(request, pk):
    """
    GET/PUT/PATCH/DELETE for a single PaymentPlan by ID
    
    - SUPER_ADMIN: Full access to all plans
    - DISTRIBUTOR: Full access to own plans
    - AGENT: Read-only access to plans from their distributor
    """
    user = request.user
    payment_plan = get_object_or_404(
        PaymentPlan.objects.select_related('distributor'),
        pk=pk
    )

    # Authorization checks
    if user.user_type == 'SUPER_ADMIN':
        pass  # Full access
    elif user.user_type == 'DISTRIBUTOR':
        if payment_plan.distributor != user:
            raise PermissionDenied("You don't own this payment plan.")
    elif user.user_type == 'AGENT':
        if not user.distributor or user.distributor != payment_plan.distributor:
            raise PermissionDenied("This plan isn't from your distributor.")
    else:
        raise PermissionDenied("Invalid user type for this operation.")

    if request.method == 'GET':
        serializer = PaymentPlanSerializer(payment_plan)
        return Response(serializer.data)

    # Modification operations require ownership or superadmin
    if user.user_type not in ['SUPER_ADMIN', 'DISTRIBUTOR']:
        raise PermissionDenied("You don't have modification permissions.")

    if request.method in ['PUT', 'PATCH']:
        serializer = PaymentPlanSerializer(
            payment_plan,
            data=request.data,
            partial=(request.method == 'PATCH'),
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Validate distributor changes for non-superadmins
        if 'distributor' in serializer.validated_data and user.user_type != 'SUPER_ADMIN':
            new_distributor = serializer.validated_data['distributor']
            if new_distributor != payment_plan.distributor:
                raise PermissionDenied("You cannot transfer payment plans to other distributors.")

        serializer.save()
        return Response(serializer.data)

    elif request.method == 'DELETE':
        payment_plan.delete()
        return Response(
            {'message': 'Payment plan deleted successfully'},
            status=status.HTTP_200_OK
        )