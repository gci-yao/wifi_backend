# wifi_app/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils.timezone import now
from datetime import timedelta
import requests

from .models import Payment, WifiSession

# 🔓 INIT PAIEMENT
@api_view(['POST'])
def init_wave_payment(request):
    phone = request.data.get("phone")
    amount = request.data.get("amount")
    commune = request.data.get("commune")
    router_name = request.data.get("router_name")

    if not phone:
        return Response({"error": "Le numéro de téléphone est obligatoire."}, status=400)
    if amount not in [200, 400]:
        return Response({"error": "Montant invalide"}, status=400)

    # MAC aléatoire
    import time
    mac = f"AA:BB:CC:{int(time.time())%100:02}:{int(time.time()*3)%100:02}:{int(time.time()*7)%100:02}"

    payment = Payment.objects.create(phone=phone, amount=amount, status="PENDING", mac=mac, commune=commune,router_name=router_name)
    

    # Lien Wave marchand réel
    wave_url = f"https://pay.wave.com/m/M_ci_rpkTnEMdLOa-/c/ci/?amount={amount}&mac={mac}&phone={phone}"

    return Response({"wave_url": wave_url, "payment_id": payment.id, "mac": mac})

# 🔒 CONFIRMATION PAIEMENT (Admin)
@api_view(['POST'])
def confirm_payment(request):
    payment_id = request.data.get("payment_id")
    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return Response({"success": False, "error": "Paiement introuvable."})

    if payment.status != "SUCCESS":
        return Response({"success": False, "error": "Paiement non confirmé par l'admin."})

    # Créer la session Wi-Fi automatiquement
    hours = 24 if payment.amount == 200 else 48
    session = WifiSession.objects.create(
        phone=payment.phone,
        mac_address=payment.mac,
        amount=payment.amount,
        end_time=now() + timedelta(hours=hours),
        is_active=True,
        commune=payment.commune,
        router_name=payment.router_name
    )

    # Appel MikroTik API pour autoriser le MAC
    # Remplace les champs ci-dessous par tes infos MikroTik
    mikrotik_url = "http://IP_DU_ROUTEUR_API_HOTSPOT/add_user"
    mikrotik_payload = {
        "mac": session.mac_address,
        "profile": "wifi24h" if hours == 24 else "wifi48h",
        "comment": f"{session.phone}"
    }
    # requests.post(mikrotik_url, json=mikrotik_payload, auth=("admin", "password"))

    return Response({"success": True, "mac": session.mac_address})

# 🔓 CHECK ACCÈS (MikroTik)
@api_view(['GET'])
def check_access(request):
    mac = request.GET.get("mac")
    session = WifiSession.objects.filter(mac_address=mac, is_active=True, end_time__gt=now()).first()
    return Response({"access": bool(session)})
