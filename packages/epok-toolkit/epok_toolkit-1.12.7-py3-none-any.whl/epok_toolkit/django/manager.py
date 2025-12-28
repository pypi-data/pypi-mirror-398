from django.db import models

class OptimizedQuerySet(models.QuerySet):
    def optimized(self, select_fields=None, prefetch_fields=None):
        qs = self
        if select_fields:
            qs = qs.select_related(*select_fields)
        if prefetch_fields:
            qs = qs.prefetch_related(*prefetch_fields)
        return qs


class OptimizedManager(models.Manager):
    """
    Custom manager for optimized querysets.
    """
    def __init__(self, select_fields_full=None, prefetch_fields_full=None, select_fields_simple=None, prefetch_fields_simple=None, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self._select_fields_full = select_fields_full or []
        self._prefetch_fields_full = prefetch_fields_full   or []
        self._select_fields_simple = select_fields_simple or []
        self._prefetch_fields_simple = prefetch_fields_simple or []

    def get_queryset(self):
        return OptimizedQuerySet(self.model, using=self._db)

    def full(self):
        return self.get_queryset().optimized(
            select_fields=self._select_fields_full,
            prefetch_fields=self._prefetch_fields_full
        )

    def simple(self):
        return self.get_queryset().optimized(
            select_fields=self._select_fields_simple,
            prefetch_fields=self._prefetch_fields_simple
        )