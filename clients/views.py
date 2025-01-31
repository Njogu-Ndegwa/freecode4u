# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

from .models import Customer
from .serializers import CustomerSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def customer_list_create_view(request):
    """
    Handle GET (list) and POST (create) for Customer.

    - GET:
      * SUPER_ADMIN => all customers
      * DISTRIBUTOR => only their own customers
      * AGENT => only customers assigned to them

    - POST (create):
      * SUPER_ADMIN => not allowed (PermissionDenied)
      * DISTRIBUTOR => can create (sets itself as .distributor)
      * AGENT => can create (sets .distributor = agent's distributor)
    """
    user = request.user

    if request.method == 'GET':
        if user.user_type == 'SUPER_ADMIN':
            queryset = Customer.objects.all()
        elif user.user_type == 'DISTRIBUTOR':
            queryset = Customer.objects.filter(distributor=user)
        elif user.user_type == 'AGENT':
            queryset = Customer.objects.filter(assigned_agent=user)
        else:
            queryset = Customer.objects.none()

        serializer = CustomerSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        # Only distributor or agent can create
        if user.user_type == 'SUPER_ADMIN':
            raise PermissionDenied("Super Admins cannot create customers.")
        
        serializer = CustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if user.user_type == 'DISTRIBUTOR':
            # The distributor is the owner
            serializer.save(distributor=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif user.user_type == 'AGENT':
            # The agent’s “distributor” field must exist
            if not user.distributor:
                raise PermissionDenied("You do not have an associated distributor.")
            serializer.save(
                distributor=user.distributor,
                assigned_agent=user
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        else:
            # Any other user types not allowed
            raise PermissionDenied("You do not have permission to create customers.")


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def customer_detail_view(request, pk):
    """
    Retrieve, update, or delete a single Customer by ID (pk).

    Visibility rules:
      * SUPER_ADMIN => can see or modify all
      * DISTRIBUTOR => can only see/modify customers they own
      * AGENT => can only see customers assigned to them (and typically can't update/delete unless you allow it)
    """
    user = request.user
    customer = get_object_or_404(Customer, pk=pk)

    # Check view permission
    if user.user_type == 'SUPER_ADMIN':
        pass  # can view any customer
    elif user.user_type == 'DISTRIBUTOR':
        if customer.distributor != user:
            raise PermissionDenied("You do not own this customer.")
    elif user.user_type == 'AGENT':
        if customer.assigned_agent != user:
            raise PermissionDenied("You do not have this customer assigned.")
    else:
        raise PermissionDenied("You do not have permission to view this customer.")

    if request.method == 'GET':
        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        # Decide if you want to let Super Admin or Distributor edit
        # For example:
        if user.user_type == 'AGENT':
            raise PermissionDenied("Agents cannot update customer data.")
        # Or if you want to forbid Super Admin as well, remove the pass below
        # if user.user_type == 'SUPER_ADMIN':
        #     raise PermissionDenied("Super Admin cannot edit customers either.")
        
        serializer = CustomerSerializer(
            customer,
            data=request.data,
            partial=(request.method == 'PATCH')
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        # Typically let only Super Admin or the owning Distributor delete
        if user.user_type == 'AGENT':
            raise PermissionDenied("Agents cannot delete customers.")
        customer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_multiple_customers_view(request):
    """
    POST /customers/assign_agent/
    {
      "agent_id": <int>,
      "customer_ids": [<int>, <int>, ...]
    }

    - Only the Distributor who owns each of those customers can assign them.
    - Each customer is assigned to the given agent, but if a customer is already
      assigned to someone else, we block and record an error.
    """
    user = request.user

    # Ensure only Distributors can assign
    if user.user_type != 'DISTRIBUTOR':
        raise PermissionDenied("Only a Distributor can assign an agent to customers.")

    agent_id = request.data.get('agent_id')
    customer_ids = request.data.get('customer_ids', [])

    if not agent_id:
        return Response(
            {"detail": "agent_id is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not isinstance(customer_ids, list) or len(customer_ids) == 0:
        return Response(
            {"detail": "customer_ids must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate the agent exists and is actually an AGENT
    try:
        agent_user = User.objects.get(pk=agent_id, user_type='AGENT')
    except ObjectDoesNotExist:
        return Response(
            {"detail": "Invalid agent_id or user is not an agent."},
            status=status.HTTP_400_BAD_REQUEST
        )

    assigned_successfully = []
    errors = []

    # Loop over each customer ID to assign
    for cid in customer_ids:
        try:
            customer = Customer.objects.get(pk=cid)
        except Customer.DoesNotExist:
            errors.append({"customer_id": cid, "detail": "Customer does not exist."})
            continue

        # Ensure this distributor owns the customer
        if customer.distributor != user:
            errors.append({
                "customer_id": cid,
                "detail": "You do not own this customer."
            })
            continue

        # If the customer already has a different agent assigned, block reassign
        if customer.assigned_agent and customer.assigned_agent != agent_user:
            errors.append({
                "customer_id": cid,
                "detail": (
                    f"This customer is already assigned to "
                    f"{customer.assigned_agent.username or 'another agent'}. "
                )
            })
            continue

        # Otherwise, assign this agent
        customer.assigned_agent = agent_user
        customer.save()
        assigned_successfully.append(cid)

    response_data = {
        "assigned": assigned_successfully,
        "errors": errors
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reassign_multiple_customers_view(request):
    """
    POST /customers/reassign_agent/
    {
      "new_agent_id": <int>,
      "customer_ids": [<int>, <int>, ...]
    }

    Reassign multiple customers (owned by the current distributor)
    from their existing assigned_agent (who can be anything) 
    to a new agent (new_agent_id).
    
    Only a Distributor can perform this. If a customer doesn't
    belong to the distributor, or the new_agent_id is not an AGENT, 
    an error is recorded for that item.
    """
    user = request.user

    # Only distributors can reassign
    if user.user_type != 'DISTRIBUTOR':
        raise PermissionDenied("Only a Distributor can reassign agents to customers.")

    # Extract data from request
    new_agent_id = request.data.get('new_agent_id')
    customer_ids = request.data.get('customer_ids', [])

    if not new_agent_id:
        return Response({"detail": "new_agent_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    if not isinstance(customer_ids, list) or len(customer_ids) == 0:
        return Response({"detail": "customer_ids must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

    # Ensure new_agent_id references a valid AGENT
    try:
        new_agent_user = User.objects.get(pk=new_agent_id, user_type='AGENT')
    except ObjectDoesNotExist:
        return Response(
            {"detail": "Invalid new_agent_id or user is not an AGENT."},
            status=status.HTTP_400_BAD_REQUEST
        )

    assigned_successfully = []
    errors = []

    for cid in customer_ids:
        try:
            customer = Customer.objects.get(pk=cid)
        except Customer.DoesNotExist:
            errors.append({
                "customer_id": cid,
                "detail": "Customer does not exist."
            })
            continue

        # Must be owned by this distributor
        if customer.distributor != user:
            errors.append({
                "customer_id": cid,
                "detail": "You do not own this customer."
            })
            continue

        # If you want to block reassigning from the same agent, uncomment:
        # if customer.assigned_agent == new_agent_user:
        #     errors.append({
        #         "customer_id": cid,
        #         "detail": "Customer is already assigned to this agent."
        #     })
        #     continue

        # Reassign the customer to the new agent
        old_agent = customer.assigned_agent
        customer.assigned_agent = new_agent_user
        customer.save()

        assigned_successfully.append({
            "customer_id": cid,
            "old_agent_id": old_agent.pk if old_agent else None
        })

    response_data = {
        "reassigned": assigned_successfully,
        "errors": errors
    }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def mac_address_view(request):
    # Get MAC address from query parameters
    mac_address = request.query_params.get('mac', None)
    
    if mac_address:
        print(f"Received MAC address: {mac_address}")  # Prints to console
        return Response(
            {"status": "success", "mac_address": mac_address},
            status=status.HTTP_200_OK
        )
    
    return Response(
        {"status": "error", "message": "MAC address not provided"},
        status=status.HTTP_400_BAD_REQUEST
    )