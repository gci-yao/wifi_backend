# wifi_app/admin.py
from django.contrib import admin
from .models import Payment, WifiSession

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("phone", "amount", "status", "mac", "created_at","commune","router_name")
    list_editable = ("status",)  # L'admin peut changer PENDING → SUCCESS

@admin.register(WifiSession)
class WifiSessionAdmin(admin.ModelAdmin):
    list_display = ("phone", "mac_address", "amount", "start_time", "end_time", "is_active","commune","router_name")
