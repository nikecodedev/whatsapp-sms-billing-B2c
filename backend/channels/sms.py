from dataclasses import dataclass
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from core.config import settings


@dataclass
class SendResult:
    success: bool
    message_id: str | None
    error: str | None


def send_sms(phone: str, message: str) -> SendResult:
    """Send SMS via Twilio. Sync because Twilio SDK is synchronous."""
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return SendResult(success=False, message_id=None, error="Twilio credentials not configured")

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=settings.TWILIO_FROM_NUMBER,
            to=phone,
        )
        return SendResult(success=True, message_id=msg.sid, error=None)
    except TwilioRestException as e:
        return SendResult(success=False, message_id=None, error=f"Twilio error {e.code}: {e.msg}")
    except Exception as e:
        return SendResult(success=False, message_id=None, error=str(e))
