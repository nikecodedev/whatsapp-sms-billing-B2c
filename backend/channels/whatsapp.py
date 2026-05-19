import httpx
from dataclasses import dataclass
from core.config import settings


@dataclass
class SendResult:
    success: bool
    message_id: str | None
    error: str | None


async def send_whatsapp(phone: str, message: str) -> SendResult:
    """Send a WhatsApp message via Z-API."""
    if not settings.ZAPI_INSTANCE_ID or not settings.ZAPI_TOKEN:
        return SendResult(success=False, message_id=None, error="Z-API credentials not configured")

    url = (
        f"{settings.ZAPI_BASE_URL}/instances/{settings.ZAPI_INSTANCE_ID}"
        f"/token/{settings.ZAPI_TOKEN}/send-text"
    )
    headers = {"Client-Token": settings.ZAPI_CLIENT_TOKEN, "Content-Type": "application/json"}
    payload = {"phone": phone, "message": message}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return SendResult(success=True, message_id=data.get("zaapId"), error=None)
        except httpx.HTTPStatusError as e:
            return SendResult(success=False, message_id=None, error=f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            return SendResult(success=False, message_id=None, error=str(e))
