# models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=20, unique=True)

    # The user who "owns" this customer (must be a DISTRIBUTOR user_type)
    distributor = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='distributor_customers'
    )

    # The agent to whom this customer is assigned (must be an AGENT user_type)
    assigned_agent = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='agent_customers'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (owned by {self.distributor}, assigned to {self.assigned_agent})"
