# models.py
from django.db import models
from django.contrib.auth.models import User  # or your custom user model

class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    symbol = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.symbol} - {self.price}"
    
class Sector(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Stock(models.Model):
    ticker = models.CharField(max_length=10)
    sic_code = models.IntegerField()
    sector = models.ForeignKey(Sector, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.ticker
    
class SicCode(models.Model):
    code = models.IntegerField()
    sector = models.ForeignKey(Sector, null=True, blank=True, on_delete=models.SET_NULL)
