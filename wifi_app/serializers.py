from rest_framework import serializers
from .models import Payment, WifiSession

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"

class WifiSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WifiSession
        fields = "__all__"
