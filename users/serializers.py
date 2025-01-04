# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
User = get_user_model()

# class LoginSerializer(serializers.Serializer):
#     username = serializers.CharField()
#     password = serializers.CharField(write_only=True)

# class LoginSerializer(TokenObtainPairSerializer):
#     """
#     Custom LoginSerializer that mimics your existing fields
#     but returns a JWT instead of using Django sessions.
#     """
#     # If you only want to enforce usage of `username` and `password`:
#     username = serializers.CharField()
#     password = serializers.CharField()

#     def validate(self, attrs):
#         # 1) Manually authenticate the user
#         user = authenticate(
#             username=attrs.get('username'),
#             password=attrs.get('password')
#         )
#         if not user:
#             raise AuthenticationFailed("Invalid credentials.")

#         if not user.is_active:
#             raise AuthenticationFailed("Account is disabled.")

#         # 2) Generate token using the built-in method on parent class
#         #    This "get_token()" returns a RefreshToken instance
#         refresh = self.get_token(user)

#         # 3) Build the final response data
#         data = {
#             'refresh': str(refresh),
#             'access': str(refresh.access_token),
#             'id': user.id,
#             'username': user.username,
#             'email': user.email,
#             'user_type': user.user_type,
#         }
#         return data

# class LoginSerializer(TokenObtainPairSerializer):
#     email = serializers.EmailField()
#     password = serializers.CharField()

#     def validate(self, attrs):
#         # Use authenticate with the "username" param actually holding the email
#         user = authenticate(username=attrs['email'], password=attrs['password'])
#         if not user:
#             raise AuthenticationFailed("Invalid credentials.")
#         if not user.is_active:
#             raise AuthenticationFailed("Account is disabled.")

#         refresh = self.get_token(user)
#         return {
#             'refresh': str(refresh),
#             'access': str(refresh.access_token),
#             'id': user.id,
#             'username': user.username,
#             'email': user.email,
#             'user_type': user.user_type,
#         }

class LoginSerializer(TokenObtainPairSerializer):
    # We tell SimpleJWT which field to treat as the "username"
    username_field = 'email'
    
    # Override the default fields so that DRF doesn't expect "username"
    email = serializers.EmailField()
    password = serializers.CharField()

    def get_token(self, user):
        """
        Override get_token to add custom claims to the token
        Note: Changed from classmethod to instance method
        """
        token = super().get_token(user)

        # Add custom claims
        token.payload['username'] = user.username
        token.payload['email'] = user.email
        token.payload['user_type'] = user.user_type

        return token

    def validate(self, attrs):
        """
        We override `validate()` so that we can:
        1) authenticate by email + password
        2) return the custom response payload (tokens + user info)
        """
        # Collect credentials for `authenticate()`
        credentials = {
            self.username_field: attrs.get('email'),
            'password': attrs.get('password'),
        }

        # Use Django's authenticate with our credentials
        user = authenticate(**credentials)

        if not user:
            raise AuthenticationFailed("Invalid credentials.")
        if not user.is_active:
            raise AuthenticationFailed("Account is disabled.")

        # Generate refresh/access tokens
        refresh = self.get_token(user)

        # Return the token + any extra user info
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'user_type': user.user_type,
        }
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'user_type', 'distributor')
        read_only_fields = ('user_type',)

class DistributorRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        # Only superadmin can create distributors
        request = self.context.get('request')
        if not request.user.user_type == 'SUPER_ADMIN':
            raise PermissionDenied("Only Super Admins can create Distributors")
            
        user = User.objects.create_user(
            **validated_data,
            user_type='DISTRIBUTOR',
            is_active=True
        )
        return user

class AgentRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'created_at', 'updated_at')

    def create(self, validated_data):
        # Only distributor can create agents
        request = self.context.get('request')
        if not request.user.user_type == 'DISTRIBUTOR':
            raise PermissionDenied("Only Distributors can create Agents")
            
        user = User.objects.create_user(
            **validated_data,
            user_type='AGENT',
            distributor=request.user,
            is_active=True
        )
        return user
    
# serializers.py

class SuperAdminRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'created_at', 'updated_at')

    def create(self, validated_data):
        request = self.context.get('request')

        # Check that the person attempting this creation is allowed
        # Commonly, you'd only allow an *existing* SUPER_ADMIN to create another SUPER_ADMIN.
        if not request.user.user_type == 'SUPER_ADMIN':
            raise PermissionDenied("Only Super Admins can create other Super Admins.")

        user = User.objects.create_user(
            **validated_data,
            user_type='SUPER_ADMIN',
            is_active=True
        )
        return user
