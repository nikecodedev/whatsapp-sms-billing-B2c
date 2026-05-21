from dataclasses import dataclass
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from core.config import settings


@dataclass
class SendResult:
    success: bool
    message_id: str | None
    error: str | None


def _public_base() -> str:
    return (settings.PUBLIC_BASE_URL or settings.APP_BASE_URL).rstrip("/")


def _from_number() -> str:
    return settings.TWILIO_VOICE_FROM_NUMBER or settings.TWILIO_FROM_NUMBER


def place_call(phone: str, contact_id: str) -> SendResult:
    """Place an outbound voice call. Twilio fetches TwiML from our webhook
    using contact_id to look up the AI-generated message."""
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return SendResult(success=False, message_id=None, error="Twilio credentials not configured")
    if not _from_number():
        return SendResult(success=False, message_id=None, error="Twilio voice from-number not configured")

    twiml_url = f"{_public_base()}/webhooks/voice/twiml/{contact_id}"
    status_callback_url = f"{_public_base()}/webhooks/voice/status/{contact_id}"

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            to=phone,
            from_=_from_number(),
            url=twiml_url,
            status_callback=status_callback_url,
            status_callback_event=["completed", "no-answer", "busy", "failed"],
            status_callback_method="POST",
        )
        return SendResult(success=True, message_id=call.sid, error=None)
    except TwilioRestException as e:
        return SendResult(success=False, message_id=None, error=f"Twilio error {e.code}: {e.msg}")
    except Exception as e:
        return SendResult(success=False, message_id=None, error=str(e))
