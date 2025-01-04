from django.db import models

class BaseModel(models.Model):
    """
    Base model with common fields: created_at, updated_at, deleted_status.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    deleted_status = models.BooleanField(default=False, verbose_name="Deleted Status")

    class Meta:
        abstract = True  