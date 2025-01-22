from django.db import models
from django.utils import timezone

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_status=False)
    

class BaseModel(models.Model):
    """
    Base model with common fields: created_at, updated_at, deleted_status.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    deleted_status = models.BooleanField(default=False, verbose_name="Deleted Status")
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.deleted_status = True
        self.save()

    class Meta:
        abstract = True  