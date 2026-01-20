# wifi_app/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils.timezone import now
from datetime import timedelta
import requests
import time

from .models import Payment, WifiSession

# 🔓 INIT PAIEMENT - Crée un paiement et retourne le lien Wave
@api_view(['POST'])
def init_wave_payment(request):
    phone = request.data.get("phone")
    amount = request.data.get("amount")
    commune = request.data.get("commune")
    router_name = request.data.get("router_name")

    # ❌ Vérifications de base
    if not phone:
        return Response({"error": "Le numéro de téléphone est obligatoire."}, status=400)

    # Montants autorisés (tu peux ajouter 500, 1000, etc.)
    if amount not in [200, 400, 500, 1000, 3000, 5000]:
        return Response({"error": "Montant invalide"}, status=400)

    # 🔹 Génération d’un MAC aléatoire simple
    mac = f"AA:BB:CC:{int(time.time())%100:02}:{int(time.time()*3)%100:02}:{int(time.time()*7)%100:02}"

    # 🔹 Création du paiement en base
    payment = Payment.objects.create(
        phone=phone,
        amount=amount,
        status="PENDING",  # En attente de confirmation admin
        mac=mac,
        commune=commune,
        router_name=router_name
    )

    # 🔹 Lien Wave marchand (à remplacer par ton vrai lien)
    wave_url = f"https://pay.wave.com/m/M_ci_rpkTnEMdLOa-/c/ci/?amount={amount}&mac={mac}&phone={phone}"

    return Response({"wave_url": wave_url, "payment_id": payment.id, "mac": mac})


# 🔒 CONFIRMATION PAIEMENT (Admin ou IA)
@api_view(['POST'])
def confirm_payment(request):
    payment_id = request.data.get("payment_id")

    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return Response({"success": False, "error": "Paiement introuvable."})

    # Vérifie que le paiement a été validé
    if payment.status != "SUCCESS":
        return Response({"success": False, "error": "Paiement non confirmé par l'admin."})

    # 🔹 Durée selon montant
    hours_mapping = {
        200: 24,
        400: 48,
        500: 72,
        1000: 168,
        3000: 720,
        5000: 1440
    }
    hours = hours_mapping.get(payment.amount, 24)

    # 🔹 Création automatique de la session Wi-Fi
    session = WifiSession.objects.create(
        phone=payment.phone,
        mac_address=payment.mac,
        amount=payment.amount,
        end_time=now() + timedelta(hours=hours),
        is_active=True,
        commune=payment.commune,
        router_name=payment.router_name
    )

    # 🔹 Appel à l’API MikroTik pour autoriser le MAC (commenté par sécurité)
    mikrotik_url = "http://IP_DU_ROUTEUR_API_HOTSPOT/add_user"
    mikrotik_payload = {
        "mac": session.mac_address,
        "profile": f"wifi{hours}h",
        "comment": f"{session.phone}"
    }
    # requests.post(mikrotik_url, json=mikrotik_payload, auth=("admin", "password"))

    return Response({"success": True, "mac": session.mac_address})


# 🔓 CHECK ACCÈS Wi-Fi (par MAC)
@api_view(['GET'])
def check_access(request):
    mac = request.GET.get("mac")

    # Recherche d’une session active et non expirée
    session = WifiSession.objects.filter(
        mac_address=mac,
        is_active=True,
        end_time__gt=now()
    ).first()

    return Response({"access": bool(session)})
