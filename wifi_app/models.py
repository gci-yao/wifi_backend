# wifi_app/models.py
from django.db import models
from django.utils.timezone import now
from datetime import timedelta

class Payment(models.Model):
    phone = models.CharField(max_length=20)
    amount = models.IntegerField()
    commune = models.CharField(max_length=50, blank=True, null=True)
    router_name = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=10, choices=[("PENDING","Pending"),("SUCCESS","Success"),("FAILED","Failed")])
    mac = models.CharField(max_length=17, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone} - {self.amount}F - {self.status}"

class WifiSession(models.Model):
    phone = models.CharField(max_length=20)
    mac_address = models.CharField(max_length=17, unique=True)
    amount = models.IntegerField()
    start_time = models.DateTimeField(auto_now_add=True)
    commune = models.CharField(max_length=50, blank=True, null=True)
    router_name = models.CharField(max_length=50, blank=True, null=True)
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.phone} - {self.mac_address} - {'active' if self.is_active else 'expired'}"
