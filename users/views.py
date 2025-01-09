# views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import login, logout, authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions
from .serializers import (
    LoginSerializer, 
    UserSerializer, 
    DistributorRegistrationSerializer, 
    AgentRegistrationSerializer,
    SuperAdminRegistrationSerializer
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
User = get_user_model()
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def login_view(request):
#     serializer = LoginSerializer(data=request.data)
#     serializer.is_valid(raise_exception=True)
    
#     username = serializer.validated_data['username']
#     password = serializer.validated_data['password']
    
#     user = authenticate(username=username, password=password)
    
#     if user is None:
#         raise AuthenticationFailed('Invalid credentials')
    
#     if not user.is_active:
#         raise AuthenticationFailed('Account is disabled')

#     login(request, user)
    
#     return Response({
#         'user': UserSerializer(user).data,
#         'message': 'Login successful'
#     })

class LoginView(TokenObtainPairView):
    """
    Custom LoginView using our LoginSerializer
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """
        1) Validate input (username/password)
        2) Authenticate user
        3) Return tokens + any custom data
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # If the user passes validation, we have the final token data
        return Response(serializer.validated_data, status=200)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({'message': 'Logout successful'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_distributor(request):
    serializer = DistributorRegistrationSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(
        UserSerializer(user).data,
        status=status.HTTP_201_CREATED
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_agent(request):
    serializer = AgentRegistrationSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(
        UserSerializer(user).data,
        status=status.HTTP_201_CREATED
    )


# views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_super_admin(request):
    serializer = SuperAdminRegistrationSerializer(
        data=request.data, 
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(
        UserSerializer(user).data, 
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_agents_for_distributor(request):
    """
    Functional view to list all agents belonging to a distributor.
    """
    # Check if the user is a distributor
    if request.user.user_type != 'DISTRIBUTOR':
        raise PermissionDenied("Only distributors can view their agents.")

    # Retrieve all agents associated with the current distributor
    agents = User.objects.filter(distributor=request.user, user_type='AGENT')
    serializer = UserSerializer(agents, many=True)

    return Response(serializer.data)

