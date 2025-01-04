# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Manufacturer, Fleet, EncoderState
from .serializers import ManufacturerSerializer, FleetSerializer, Item, ItemSerializer
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from .models import Customer
from django.db import transaction
User = get_user_model()

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manufacturer_list_create_view(request):
    """
    Endpoint: /manufacturers/
    GET: 
      - SUPER_ADMIN => all manufacturers
      - DISTRIBUTOR => only manufacturers where distributor=user
      - AGENT => only manufacturers where distributor=user.distributor

    POST
      - DISTRIBUTOR => can create (owned by them)
      - SUPER_ADMIN => blocked (per your rules)
      - AGENT => blocked (read-only)

    {
        "name": "Manufacturer A",
        "description": "The manufacturer creates items"
    }
    """
    user = request.user

    if request.method == 'GET':
        if user.user_type == 'SUPER_ADMIN':
            queryset = Manufacturer.objects.all()
        elif user.user_type == 'DISTRIBUTOR':
            queryset = Manufacturer.objects.filter(distributor=user)
        elif user.user_type == 'AGENT':
            # Agents see the manufacturers owned by their distributor
            if not user.distributor:
                # If agent has no distributor set, they see nothing
                queryset = Manufacturer.objects.none()
            else:
                queryset = Manufacturer.objects.filter(distributor=user.distributor)
        else:
            # Other roles see none
            queryset = Manufacturer.objects.none()

        serializer = ManufacturerSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        # Only DISTRIBUTOR can create
        if user.user_type != 'DISTRIBUTOR':
            raise PermissionDenied("Only a Distributor can create a manufacturer.")

        serializer = ManufacturerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(distributor=user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def manufacturer_detail_view(request, pk):
    """
    GET/PUT/PATCH/DELETE a single Manufacturer by ID.

    - SUPER_ADMIN => can access/modify any manufacturer
    - DISTRIBUTOR => can access/modify only if they own the manufacturer
    - AGENT => can read if the manufacturer belongs to the agent's distributor, cannot modify
    """
    user = request.user
    manufacturer = get_object_or_404(Manufacturer, pk=pk)

    if request.method == 'GET':
        # Who can read?
        if user.user_type == 'SUPER_ADMIN':
            pass  # can read anything
        elif user.user_type == 'DISTRIBUTOR':
            if manufacturer.distributor != user:
                raise PermissionDenied("You do not own this manufacturer.")
        elif user.user_type == 'AGENT':
            # Agent can read only if the manufacturer belongs to agent's distributor
            if not user.distributor or (manufacturer.distributor != user.distributor):
                raise PermissionDenied("This manufacturer is not owned by your distributor.")
        else:
            raise PermissionDenied("You do not have permission to view this manufacturer.")

        serializer = ManufacturerSerializer(manufacturer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # For PUT, PATCH, DELETE => only SUPER_ADMIN or owning DISTRIBUTOR
    # Agents have read-only, so forbid these methods for AGENT

    # Check ownership / user type
    if user.user_type == 'SUPER_ADMIN':
        pass  # can update/delete anything
    elif user.user_type == 'DISTRIBUTOR':
        if manufacturer.distributor != user:
            raise PermissionDenied("You do not own this manufacturer.")
    else:
        # If AGENT or any other role tries to update/delete => 403
        raise PermissionDenied("You do not have permission to modify this manufacturer.")

    if request.method in ['PUT', 'PATCH']:
        serializer = ManufacturerSerializer(
            manufacturer,
            data=request.data,
            partial=(request.method == 'PATCH')
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        manufacturer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def fleet_list_create_view(request):
    """
    Endpoint: fleet/
    GET:
      - SUPER_ADMIN => all fleets
      - DISTRIBUTOR => only fleets they own
      - AGENT => only fleets assigned to them

    POST:
      - Only a DISTRIBUTOR can create a fleet; assigned_agent is null by default

    {
    "name": "Catturd",
    "description": "A Particular Fleet"
    }
    """
    user = request.user

    if request.method == 'GET':
        if user.user_type == 'SUPER_ADMIN':
            queryset = Fleet.objects.all()
        elif user.user_type == 'DISTRIBUTOR':
            queryset = Fleet.objects.filter(distributor=user)
        elif user.user_type == 'AGENT':
            queryset = Fleet.objects.filter(assigned_agent=user)
        else:
            queryset = Fleet.objects.none()

        serializer = FleetSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        # Only a distributor can create
        if user.user_type != 'DISTRIBUTOR':
            raise PermissionDenied("Only a Distributor can create fleets.")

        serializer = FleetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Force the distributor to the current user
        serializer.save(distributor=user, assigned_agent=None)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def fleet_detail_view(request, pk):
    """
    GET/PUT/PATCH/DELETE for a single Fleet by ID.
    
    - SUPER_ADMIN => can do anything by default (if you want)
    - DISTRIBUTOR => can only modify if they own the fleet
    - AGENT => read-only if assigned to them, cannot modify
    """
    user = request.user
    fleet = get_object_or_404(Fleet, pk=pk)

    if request.method == 'GET':
        # Checking read permission
        if user.user_type == 'SUPER_ADMIN':
            pass  # can read any
        elif user.user_type == 'DISTRIBUTOR':
            if fleet.distributor != user:
                raise PermissionDenied("You do not own this fleet.")
        elif user.user_type == 'AGENT':
            if fleet.assigned_agent != user:
                raise PermissionDenied("This fleet is not assigned to you.")
        else:
            raise PermissionDenied("You do not have permission to view fleets.")
        
        serializer = FleetSerializer(fleet)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # For PUT/PATCH/DELETE => must be the owning distributor (or superadmin, if desired)
    if user.user_type == 'SUPER_ADMIN':
        pass  # or skip pass if you want them restricted too
    elif user.user_type == 'DISTRIBUTOR':
        if fleet.distributor != user:
            raise PermissionDenied("You do not own this fleet.")
    else:
        # Agents or other roles cannot modify
        raise PermissionDenied("You do not have permission to modify fleets.")

    if request.method in ['PUT', 'PATCH']:
        serializer = FleetSerializer(
            fleet,
            data=request.data,
            partial=(request.method == 'PATCH')
        )
        serializer.is_valid(raise_exception=True)
        # distributor and assigned_agent remain as is, unless you want to allow clearing
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        fleet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_fleets_view(request):
    """
    POST /fleets/assign/
    {
      "agent_id": <int>,
      "fleet_ids": [<int>, <int>, ...]
    }

    Assign multiple currently unassigned fleets to an agent.
    - Only the distributor who owns each fleet can do this.
    - Fails if any fleet is already assigned. (We skip those or record errors)
    """
    user = request.user

    # Must be a DISTRIBUTOR
    if user.user_type != 'DISTRIBUTOR':
        raise PermissionDenied("Only a Distributor can assign fleets.")

    agent_id = request.data.get('agent_id')
    fleet_ids = request.data.get('fleet_ids', [])

    if not agent_id:
        return Response({"detail": "agent_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    if not isinstance(fleet_ids, list) or len(fleet_ids) == 0:
        return Response({"detail": "fleet_ids must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

    # Verify agent_id references a valid AGENT user
    try:
        agent_user = User.objects.get(pk=agent_id, user_type='AGENT')
        print(agent_user, "Agent User--")
    except ObjectDoesNotExist:
        return Response(
            {"detail": "Invalid agent_id or user is not an AGENT."},
            status=status.HTTP_400_BAD_REQUEST
        )

    assigned_fleets = []
    errors = []

    for fid in fleet_ids:
        try:
            fleet = Fleet.objects.get(pk=fid)
        except Fleet.DoesNotExist:
            errors.append({
                "fleet_id": fid,
                "detail": "Fleet does not exist."
            })
            continue

        # Must belong to this distributor
        if fleet.distributor != user:
            errors.append({
                "fleet_id": fid,
                "detail": "You do not own this fleet."
            })
            continue

        # Must not be already assigned
        if fleet.assigned_agent is not None:
            errors.append({
                "fleet_id": fid,
                "detail": "Fleet is already assigned. Use the reassign endpoint."
            })
            continue

        # Assign fleet
        fleet.assigned_agent = agent_user
        print(fleet, "Fleet----")
        fleet.save()
        assigned_fleets.append(fid)

    response_data = {
        "assigned_fleet_ids": assigned_fleets,
        "errors": errors
    }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reassign_fleets_view(request):
    """
    POST /fleets/reassign/
    {
      "new_agent_id": <int>,
      "fleet_ids": [<int>, <int>, ...]
    }

    Reassign multiple fleets that are currently assigned to some agent,
    to a new agent.

    - Only the distributor who owns each fleet can do this.
    - Fails if any fleet is not assigned yet or belongs to someone else.
    """
    user = request.user

    if user.user_type != 'DISTRIBUTOR':
        raise PermissionDenied("Only a Distributor can reassign fleets.")

    new_agent_id = request.data.get('new_agent_id')
    fleet_ids = request.data.get('fleet_ids', [])

    if not new_agent_id:
        return Response({"detail": "new_agent_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    if not isinstance(fleet_ids, list) or len(fleet_ids) == 0:
        return Response({"detail": "fleet_ids must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

    # Verify new_agent_id references a valid AGENT user
    try:
        new_agent_user = User.objects.get(pk=new_agent_id, user_type='AGENT')
    except ObjectDoesNotExist:
        return Response(
            {"detail": "Invalid new_agent_id or user is not an AGENT."},
            status=status.HTTP_400_BAD_REQUEST
        )

    reassigned_fleets = []
    errors = []

    for fid in fleet_ids:
        try:
            fleet = Fleet.objects.get(pk=fid)
        except Fleet.DoesNotExist:
            errors.append({
                "fleet_id": fid,
                "detail": "Fleet does not exist."
            })
            continue

        # Must belong to this distributor
        if fleet.distributor != user:
            errors.append({
                "fleet_id": fid,
                "detail": "You do not own this fleet."
            })
            continue

        # Must already be assigned to someone
        if fleet.assigned_agent is None:
            errors.append({
                "fleet_id": fid,
                "detail": "Fleet is not assigned to any agent. Use the assign endpoint."
            })
            continue

        old_agent = fleet.assigned_agent

        # Reassign
        fleet.assigned_agent = new_agent_user
        fleet.save()
        reassigned_fleets.append({
            "fleet_id": fid,
            "old_agent_id": old_agent.pk if old_agent else None
        })

    response_data = {
        "reassigned": reassigned_fleets,
        "errors": errors
    }
    return Response(response_data, status=status.HTTP_200_OK)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def create_item_view(request):
#     """
#     POST /items/create/
#     {
#       "serial_number": "XYZ123",
#       "manufacturers": 1
#       // Optionally "fleet_id" if you allow direct assignment
#     }

#     Only a DISTRIBUTOR can create an item.
#     If you want to enforce that an item must belong to a fleet,
#     you can accept a "fleet_id" here or have a separate function.
#     """
#     user = request.user

#     # 1) Must be a distributor
#     if user.user_type != 'DISTRIBUTOR':
#         raise PermissionDenied("Only a Distributor can create items.")

#     # 2) Validate incoming data
#     serializer = ItemSerializer(data=request.data)
#     serializer.is_valid(raise_exception=True)

#     # If you want to allow direct linking to a fleet at creation:
#     fleet_id = request.data.get('fleet_id')
#     if fleet_id:
#         fleet = get_object_or_404(Fleet, pk=fleet_id)
#         # Ensure the fleet belongs to this distributor
#         if fleet.distributor != user:
#             raise PermissionDenied("You do not own this fleet.")
#         # Save the item with the fleet
#         item = Item.objects.create(
#             serial_number=serializer.validated_data['serial_number'],
#             fleet=fleet
#         )
#         # If you allow many-to-many manufacturers:
#         item.manufacturers = serializer.validated_data.get('manufacturers')
#         item.save()
#     else:
#         # If you allow creating an item without a fleet, do so:
#         item = serializer.save()

#     return Response(
#         ItemSerializer(item).data,
#         status=status.HTTP_201_CREATED
#     )


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def create_items_bulk_view(request):
#     """
#     POST /items/bulk_create/
#     {
#       "items": [
#         {
#           "serial_number": "SERIAL001",
#           "fleet_id": 10,
#           "manufacturers": 1
#         },
#         {
#           "serial_number": "SERIAL002",
#           "fleet_id": 10
#         }
#       ]
#     }
#     Only a DISTRIBUTOR can bulk create items.
#     """
#     user = request.user
#     if user.user_type != 'DISTRIBUTOR':
#         raise PermissionDenied("Only a Distributor can create items.")

#     data = request.data.get('items', [])
#     if not isinstance(data, list):
#         return Response({"detail": "'items' must be a list."}, status=status.HTTP_400_BAD_REQUEST)

#     created_items = []
#     errors = []

#     for idx, item_data in enumerate(data):
#         # We can optionally pass partial data to our serializer
#         serializer = ItemSerializer(data=item_data)
#         if serializer.is_valid():
#             fleet_id = item_data.get('fleet_id')
#             if fleet_id:
#                 fleet = get_object_or_404(Fleet, pk=fleet_id)
#                 if fleet.distributor != user:
#                     errors.append({
#                         "index": idx,
#                         "error": "You do not own fleet_id={}".format(fleet_id)
#                     })
#                     continue
#                 item_obj = Item.objects.create(
#                     serial_number=serializer.validated_data['serial_number'],
#                     fleet=fleet
#                 )
#                 item_obj.manufacturers = serializer.validated_data.get('manufacturers')
#                 item_obj.save()
#             else:
#                 # create item without fleet
#                 item_obj = serializer.save()

#             created_items.append(ItemSerializer(item_obj).data)
#         else:
#             errors.append({
#                 "index": idx,
#                 "error": serializer.errors
#             })

#     return Response({
#         "created_items": created_items,
#         "errors": errors
#     }, status=status.HTTP_201_CREATED if created_items else status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_item_view(request):
    """
    POST /items/create/
    {
        "serial_number": "XYZ123",
        "manufacturers": 1,
        "encoder_state": {
            "token_type": "type1",
            "token_value": "value1",
            "secret_key": "key123",
            "starting_code": "START001",
            "max_count": 100,
            "token": "token123"
        }
    }
    """
    user = request.user

    # 1) Must be a distributor
    if user.user_type != 'DISTRIBUTOR':
        raise PermissionDenied("Only a Distributor can create items.")

    # 2) Validate incoming data
    serializer = ItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Start a transaction to ensure both item and encoder state are created or neither
    from django.db import transaction
    with transaction.atomic():
        # Create the item
        fleet_id = request.data.get('fleet_id')
        if fleet_id:
            fleet = get_object_or_404(Fleet, pk=fleet_id)
            if fleet.distributor != user:
                raise PermissionDenied("You do not own this fleet.")
            item = Item.objects.create(
                serial_number=serializer.validated_data['serial_number'],
                fleet=fleet
            )
            item.manufacturers = serializer.validated_data.get('manufacturers')
            item.save()
        else:
            item = Item.objects.create(
                serial_number=serializer.validated_data['serial_number'],
                manufacturers=serializer.validated_data.get('manufacturers')
            )

        # Create the encoder state if provided
        encoder_state_data = serializer.validated_data.get('encoder_state')
        if encoder_state_data:
            EncoderState.objects.create(item=item, **encoder_state_data)

    return Response(
        ItemSerializer(item).data,
        status=status.HTTP_201_CREATED
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_items_bulk_view(request):
    """
    POST /items/bulk_create/
    {
        "items": [
            {
                "serial_number": "SERIAL001",
                "fleet_id": 10,
                "manufacturers": 1,
                "encoder_state": {
                    "token_type": "type1",
                    "token_value": "value1",
                    "secret_key": "key123",
                    "starting_code": "START001",
                    "max_count": 100,
                    "token": "token123"
                }
            }
        ]
    }
    """
    user = request.user
    if user.user_type != 'DISTRIBUTOR':
        raise PermissionDenied("Only a Distributor can create items.")

    data = request.data.get('items', [])
    if not isinstance(data, list):
        return Response({"detail": "'items' must be a list."}, status=status.HTTP_400_BAD_REQUEST)

    created_items = []
    errors = []

    for idx, item_data in enumerate(data):
        serializer = ItemSerializer(data=item_data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    fleet_id = item_data.get('fleet_id')
                    if fleet_id:
                        fleet = get_object_or_404(Fleet, pk=fleet_id)
                        if fleet.distributor != user:
                            raise PermissionDenied(f"You do not own fleet_id={fleet_id}")

                        # Pass fleet to serializer's save method
                        item_obj = serializer.save(fleet=fleet)
                    else:
                        # Create item without fleet
                        item_obj = serializer.save()

                created_items.append(ItemSerializer(item_obj).data)
            except Exception as e:
                errors.append({
                    "index": idx,
                    "error": str(e)
                })
        else:
            errors.append({
                "index": idx,
                "error": serializer.errors
            })

    return Response({
        "created_items": created_items,
        "errors": errors
    }, status=status.HTTP_201_CREATED if created_items else status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_item_to_fleet_view(request):
    """
    POST /items/assign_fleet/
    {
      "fleet_id": <int>,
      "item_ids": [<int>, <int>, ...]
    }
    Assign multiple items (which have no fleet yet) to the given fleet.
    - Only a distributor who owns the fleet can do this.
    - If an item already has a fleet, we skip it or record an error.
    """
    user = request.user
    if user.user_type != 'DISTRIBUTOR':
        raise PermissionDenied("Only a Distributor can assign items to a fleet.")

    fleet_id = request.data.get('fleet_id')
    if not fleet_id:
        return Response({"detail": "fleet_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    fleet = get_object_or_404(Fleet, pk=fleet_id)
    if fleet.distributor != user:
        raise PermissionDenied("You do not own this fleet.")

    item_ids = request.data.get('item_ids', [])
    if not isinstance(item_ids, list) or len(item_ids) == 0:
        return Response({"detail": "Must provide a non-empty list of item_ids."}, status=status.HTTP_400_BAD_REQUEST)

    assigned = []
    errors = []

    for iid in item_ids:
        try:
            item_obj = Item.objects.get(pk=iid)
        except Item.DoesNotExist:
            errors.append({"item_id": iid, "error": "Item not found."})
            continue

        # The item must not already have a fleet.
        if item_obj.fleet is not None:
            errors.append({
                "item_id": iid,
                "error": "Item already belongs to a fleet. Use reassign endpoint."
            })
            continue

        # Assign item to this fleet
        item_obj.fleet = fleet
        item_obj.save()
        assigned.append(iid)

    return Response({
        "assigned_items": assigned,
        "errors": errors
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reassign_item_to_fleet_view(request):
    """
    POST /items/reassign_fleet/
    {
      "fleet_id": <int>,
      "item_ids": [<int>, <int>, ...]
    }
    Reassign multiple items (which already belong to some fleet) 
    to a new fleet owned by the same distributor.
    - If an item is not owned by the same distributor, skip/error.
    - If an item has no fleet yet, skip/error (they belong in the assign endpoint).
    """
    user = request.user
    if user.user_type != 'DISTRIBUTOR':
        raise PermissionDenied("Only a Distributor can reassign items to a fleet.")

    fleet_id = request.data.get('fleet_id')
    if not fleet_id:
        return Response({"detail": "fleet_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    new_fleet = get_object_or_404(Fleet, pk=fleet_id)
    if new_fleet.distributor != user:
        raise PermissionDenied("You do not own this new fleet.")

    item_ids = request.data.get('item_ids', [])
    if not isinstance(item_ids, list) or len(item_ids) == 0:
        return Response({"detail": "Must provide a non-empty list of item_ids."}, status=status.HTTP_400_BAD_REQUEST)

    reassigned = []
    errors = []

    for iid in item_ids:
        try:
            item_obj = Item.objects.get(pk=iid)
        except Item.DoesNotExist:
            errors.append({"item_id": iid, "error": "Item not found."})
            continue

        # The item must already have a fleet
        if item_obj.fleet is None:
            errors.append({
                "item_id": iid,
                "error": "Item has no fleet. Use assign endpoint instead."
            })
            continue

        # The item’s current fleet must also belong to the same distributor
        if item_obj.fleet.distributor != user:
            errors.append({
                "item_id": iid,
                "error": "Item belongs to a fleet owned by a different distributor."
            })
            continue

        # Reassign item to the new fleet
        item_obj.fleet = new_fleet
        item_obj.save()
        reassigned.append(iid)

    return Response({
        "reassigned_items": reassigned,
        "errors": errors
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_items_in_fleet_view(request, fleet_id):
    """
    GET /fleets/<fleet_id>/items/
    Returns all items in a given fleet.
    - If user is the distributor, they can see them.
    - If user is an agent assigned to that fleet, they can see them 
      (assuming you want that logic).
    - Otherwise 403.
    """
    user = request.user
    fleet = get_object_or_404(Fleet, pk=fleet_id)

    # Check permission
    if user.user_type == 'DISTRIBUTOR':
        if fleet.distributor != user:
            raise PermissionDenied("You do not own this fleet.")
    elif user.user_type == 'AGENT':
        # If you want an agent to see items if they are assigned to the fleet
        if fleet.assigned_agent != user:
            raise PermissionDenied("You do not have access to this fleet.")
    else:
        # Possibly super admin logic or block
        # raise PermissionDenied("You do not have access.")
        pass

    items = fleet.items.all()
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_distributor_items_view(request):
    """
    GET /items/distributor/
    Return all items that belong to fleets owned by the distributor.
    """
    user = request.user
    if user.user_type != 'DISTRIBUTOR':
        raise PermissionDenied("Only a Distributor can view their items.")

    # All fleets belonging to user
    fleets = user.fleets.all()
    items = Item.objects.filter(fleet__in=fleets)
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_agent_items_view(request):
    """
    GET /items/agent/
    Return all items that belong to fleets assigned to the agent.
    """
    user = request.user
    if user.user_type != 'AGENT':
        raise PermissionDenied("Only an Agent can view their items.")

    # The agent may be assigned multiple fleets
    fleets = user.assigned_fleets.all()  # from Fleet.assigned_agent
    items = Item.objects.filter(fleet__in=fleets)
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_item_view(request, item_id):
    """
    POST /items/<item_id>/buy/
    {
      "customer_id": <int>
    }

    The item is "purchased" by a customer.
    Only the distributor who owns the fleet of this item can do this.

    If the item is already purchased by a customer, 
    we do NOT allow transferring it to another customer.
    """
    user = request.user
    if user.user_type != 'DISTRIBUTOR':
        raise PermissionDenied("Only a Distributor can assign an item to a customer.")

    # Retrieve the item
    item = get_object_or_404(Item, pk=item_id)

    # Ensure the item belongs to a fleet owned by the current distributor
    if item.fleet.distributor != user:
        raise PermissionDenied("You do not own this item (through its fleet).")

    # If the item is already purchased by someone, disallow a new purchase
    if item.customer is not None:
        return Response(
            {"detail": "This item has already been purchased by another customer."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check for the new customer
    customer_id = request.data.get('customer_id')
    if not customer_id:
        return Response({"detail": "customer_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Retrieve the customer
    customer = get_object_or_404(Customer, pk=customer_id)

    # Tie the item to the customer
    item.customer = customer
    item.save()

    return Response({
        "detail": "Item has been successfully purchased by the customer.",
        "item_id": item.id,
        "customer_id": customer.id
    }, status=status.HTTP_200_OK)

