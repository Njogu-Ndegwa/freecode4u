from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from utils.models import BaseModel

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        # Normalize the email address (e.g., make all lowercase)
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
    

# class User(AbstractUser):
#     USER_TYPES = (
#         ('SUPER_ADMIN', 'Super Admin'),
#         ('DISTRIBUTOR', 'Distributor'),
#         ('AGENT', 'Agent')
#     )
    
#     # Required fields for authentication (already included in AbstractUser)
#     # - username
#     # - password
#     # - email
    
#     # Your custom fields
#     user_type = models.CharField(max_length=20, choices=USER_TYPES)
#     distributor = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='agents')
#     permissions = models.JSONField(default=dict, null=True, blank=True)
    
#     # Basic status flags
#     is_active = models.BooleanField(default=True)  # Already in AbstractUser, but important to note
#     email_verified = models.BooleanField(default=False)  # Basic email verification
    
#     # Timestamps
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['-created_at']

class User(AbstractUser, BaseModel):
    USER_TYPES = (
        ('SUPER_ADMIN', 'Super Admin'),
        ('DISTRIBUTOR', 'Distributor'),
        ('AGENT', 'Agent'),
    )

    # Remove the username field from AbstractUser
    username = None

    # Use email as the unique identifier
    email = models.EmailField(unique=True)

    # Your custom fields
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    distributor = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='agents'
    )
    is_active = models.BooleanField(default=True)
    email_verified = models.BooleanField(default=False)
    # Manager
    objects = UserManager()

    # This is crucial:
    USERNAME_FIELD = 'email'  # Now uses email instead of username
    REQUIRED_FIELDS = []       # By default, no additional mandatory fields

    class Meta:
        ordering = ['-created_at']