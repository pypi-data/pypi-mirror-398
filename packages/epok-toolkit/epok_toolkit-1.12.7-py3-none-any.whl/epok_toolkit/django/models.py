from uuid import uuid4
from django.conf import settings
from django.db import models



class UUID4Mixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    class Meta:
        abstract = True
        


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        


class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['is_deleted']),
        ]



class CreatorsMixin(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, 
                                  on_delete=models.CASCADE, related_name='%(class)s_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, 
                                  on_delete=models.CASCADE, related_name='%(class)s_updated')

    class Meta:
        abstract = True