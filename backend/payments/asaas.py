import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import httpx

from core.config import settings


@dataclass
class ChargeResult:
    asaas_id: str
    invoice_url: str
    pix_qr_code: str | None
    boleto_barcode: str | None
    status: str


async def _asaas_headers() -> dict:
    return {
        "access_token": settings.ASAAS_API_KEY,
        "Content-Type": "application/json",
    }


async def get_or_create_customer(cpf: str, nome: str, email: str | None = None) -> str:
    """Return Asaas customer ID, creating one if it doesn't exist."""
    async with httpx.AsyncClient(timeout=30) as client:
        headers = await _asaas_headers()

        # Search for existing customer by CPF
        resp = await client.get(
            f"{settings.ASAAS_BASE_URL}/customers",
            params={"cpfCnpj": cpf},
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("data"):
            return data["data"][0]["id"]

        # Create new customer
        payload = {"name": nome, "cpfCnpj": cpf}
        if email:
            payload["email"] = email

        resp = await client.post(
            f"{settings.ASAAS_BASE_URL}/customers",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()["id"]


async def create_pix_charge(
    customer_id: str,
    amount: Decimal,
    due_date: date,
    description: str,
    external_reference: str,
) -> ChargeResult:
    async with httpx.AsyncClient(timeout=30) as client:
        headers = await _asaas_headers()
        payload = {
            "customer": customer_id,
            "billingType": "PIX",
            "value": float(amount),
            "dueDate": due_date.strftime("%Y-%m-%d"),
            "description": description,
            "externalReference": external_reference,
        }
        resp = await client.post(f"{settings.ASAAS_BASE_URL}/payments", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        # Fetch PIX QR code
        qr_resp = await client.get(
            f"{settings.ASAAS_BASE_URL}/payments/{data['id']}/pixQrCode",
            headers=headers,
        )
        qr_data = qr_resp.json() if qr_resp.status_code == 200 else {}

        return ChargeResult(
            asaas_id=data["id"],
            invoice_url=data.get("invoiceUrl", ""),
            pix_qr_code=qr_data.get("payload"),
            boleto_barcode=None,
            status=data.get("status", "PENDING"),
        )


async def create_boleto_charge(
    customer_id: str,
    amount: Decimal,
    due_date: date,
    description: str,
    external_reference: str,
) -> ChargeResult:
    async with httpx.AsyncClient(timeout=30) as client:
        headers = await _asaas_headers()
        payload = {
            "customer": customer_id,
            "billingType": "BOLETO",
            "value": float(amount),
            "dueDate": due_date.strftime("%Y-%m-%d"),
            "description": description,
            "externalReference": external_reference,
        }
        resp = await client.post(f"{settings.ASAAS_BASE_URL}/payments", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        return ChargeResult(
            asaas_id=data["id"],
            invoice_url=data.get("invoiceUrl", ""),
            pix_qr_code=None,
            boleto_barcode=data.get("bankSlipUrl"),
            status=data.get("status", "PENDING"),
        )


async def get_payment_status(asaas_id: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        headers = await _asaas_headers()
        resp = await client.get(f"{settings.ASAAS_BASE_URL}/payments/{asaas_id}", headers=headers)
        resp.raise_for_status()
        return resp.json().get("status", "PENDING")
