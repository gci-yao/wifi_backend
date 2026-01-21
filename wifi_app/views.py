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

    if amount not in [200, 400, 500, 1000, 3000, 5000]:
        return Response({"error": "Montant invalide"}, status=400)

    # ❌ Empêche plusieurs paiements PENDING pour un même numéro
    if Payment.objects.filter(phone=phone, status="PENDING").exists():
        return Response({"error": "Un paiement est déjà en attente pour ce numéro."}, status=400)

    # 🔹 Génération MAC pseudo-unique
    mac = f"AA:BB:CC:{int(time.time())%100:02}:{int(time.time()*3)%100:02}:{int(time.time()*7)%100:02}"

    # 🔹 Création paiement en base
    payment = Payment.objects.create(
        phone=phone,
        amount=amount,
        status="PENDING",
        mac=mac,
        commune=commune,
        router_name=router_name
    )

    # 🔹 Lien Wave marchand (REMPLACE PAR TON LIEN RÉEL)
    wave_url = f"https://pay.wave.com/m/M_ci_rpkTnEMdLOa-/c/ci/?amount={amount}&mac={mac}&phone={phone}"

    return Response({
        "wave_url": wave_url,
        "payment_id": payment.id,
        "mac": mac
    })


# 🔒 CONFIRMATION PAIEMENT (Admin / IA)
@api_view(['POST'])
def confirm_payment(request):
    payment_id = request.data.get("payment_id")

    if not payment_id:
        return Response({"success": False, "status": "ERROR", "message": "payment_id manquant"}, status=400)

    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return Response({"success": False, "status": "ERROR", "message": "Paiement introuvable"}, status=404)

    # ❌ ADMIN A REFUSÉ
    if payment.status == "FAILED":
        return Response({
            "success": False,
            "status": "FAILED",
            "message": "Vous n'avez pas payé. Veuillez actualiser la page."
        })

    # ⏳ PAS ENCORE VALIDÉ
    if payment.status == "PENDING":
        return Response({
            "success": False,
            "status": "PENDING",
            "message": "Paiement en attente de validation admin."
        })

    # ✅ ADMIN A CONFIRMÉ
    if payment.status == "SUCCESS":

        hours_mapping = {
            200: 24,
            400: 48,
            500: 72,
            1000: 168,
            3000: 720,
            5000: 1440
        }
        hours = hours_mapping.get(payment.amount, 24)

        # 🔹 Création ou récupération session Wi-Fi
        session, created = WifiSession.objects.get_or_create(
            mac_address=payment.mac,
            defaults={
                "phone": payment.phone,
                "amount": payment.amount,
                "end_time": now() + timedelta(hours=hours),
                "is_active": True,
                "commune": payment.commune,
                "router_name": payment.router_name,
            }
        )

        # 🔹 APPEL MIKROTIK (À ACTIVER PLUS TARD)
        mikrotik_url = "http://IP_DU_ROUTEUR_API_HOTSPOT/add_user"
        mikrotik_payload = {
            "mac": session.mac_address,
            "profile": f"wifi{hours}h",
            "comment": f"{session.phone}"
        }

        # requests.post(mikrotik_url, json=mikrotik_payload, auth=("admin", "password"))

        return Response({
            "success": True,
            "status": "SUCCESS",
            "mac": session.mac_address
        })


# 🔓 CHECK ACCÈS Wi-Fi (appelé par MikroTik)
@api_view(['GET'])
def check_access(request):
    mac = request.GET.get("mac")

    session = WifiSession.objects.filter(
        mac_address=mac,
        is_active=True,
        end_time__gt=now()
    ).first()

    return Response({
        "access": bool(session)
    })
