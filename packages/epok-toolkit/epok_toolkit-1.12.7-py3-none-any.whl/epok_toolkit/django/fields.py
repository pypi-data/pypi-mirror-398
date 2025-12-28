from django.db import models
from decimal import Decimal

class StandarFloatField(models.FloatField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', 0.0)
        super().__init__(*args, **kwargs)

class StandarDecimalField(models.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_digits', 10)
        kwargs.setdefault('decimal_places', 2)
        kwargs.setdefault('default', Decimal('0.00'))
        super().__init__(*args, **kwargs)

class StandarIntegerField(models.IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', 0)
        super().__init__(*args, **kwargs)

class StandarCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 20)
        kwargs.setdefault('default', 'Not specified')
        super().__init__(*args, **kwargs)
        
class StandarDateTimeField(models.DateTimeField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_now_add', True)
        super().__init__(*args, **kwargs)