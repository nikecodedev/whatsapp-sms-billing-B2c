import json
import re
from dataclasses import dataclass
from datetime import datetime, date

import anthropic

from core.config import settings
from .prompts import DECISION_SYSTEM_PROMPT, DECISION_USER_TEMPLATE


@dataclass
class ContactDecision:
    channel: str       # whatsapp | sms | call
    tone: str          # amigavel | neutro | formal | urgente
    send_time: str     # "HH:MM"
    message: str       # full message text with [PAYMENT_LINK] placeholder
    reasoning: str


# AsyncAnthropic — sync calls in an async context block the event loop
# (the entire backend stops serving requests during the API call).
_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


def _days_overdue(due_date: date) -> int:
    return max(0, (date.today() - due_date).days)


def _build_historico(contacts: list[dict]) -> str:
    if not contacts:
        return "Nenhuma tentativa anterior"
    lines = []
    for c in contacts[-5:]:  # last 5 attempts
        lines.append(f"  - {c['channel']} em {c['sent_at']}: {c['status']}")
    return "\n".join(lines)


def _determine_current_channel(
    attempt_number: int,
    max_whatsapp: int,
    max_sms: int,
    canal_preferencial: str | None,
) -> tuple[str, int, int]:
    """Returns (channel, attempt_in_channel, max_in_channel)."""
    if canal_preferencial == "sms":
        if attempt_number <= max_sms:
            return "sms", attempt_number, max_sms
        return "call", attempt_number - max_sms, 1

    if canal_preferencial == "call":
        return "call", 1, 1

    # Default: WhatsApp → SMS → Call
    if attempt_number <= max_whatsapp:
        return "whatsapp", attempt_number, max_whatsapp
    elif attempt_number <= max_whatsapp + max_sms:
        return "sms", attempt_number - max_whatsapp, max_sms
    else:
        return "call", 1, 1


async def decide_contact(
    nome_completo: str,
    valor_divida: float,
    data_vencimento: date,
    canal_preferencial: str | None,
    permite_parcelamento: bool,
    attempt_number: int,
    max_whatsapp: int,
    max_sms: int,
    previous_contacts: list[dict],
    observacoes: str | None = None,
) -> ContactDecision:
    dias_atraso = _days_overdue(data_vencimento)
    current_channel, attempt_in_channel, max_in_channel = _determine_current_channel(
        attempt_number, max_whatsapp, max_sms, canal_preferencial
    )

    user_content = DECISION_USER_TEMPLATE.format(
        nome_completo=nome_completo,
        valor_divida=f"{valor_divida:,.2f}",
        data_vencimento=data_vencimento.strftime("%d/%m/%Y"),
        dias_atraso=dias_atraso,
        canal_preferencial=canal_preferencial or "sem preferência",
        permite_parcelamento="Sim" if permite_parcelamento else "Não",
        attempt_number=attempt_in_channel,
        max_attempts=max_in_channel,
        current_channel=current_channel,
        historico=_build_historico(previous_contacts),
        observacoes=observacoes or "Nenhuma",
        hora_atual=datetime.now().strftime("%H:%M"),
    )

    response = await _client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=1024,
        system=DECISION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = response.content[0].text.strip()

    # Extract JSON even if Claude wraps it in markdown code blocks
    json_match = re.search(r"\{[\s\S]*\}", raw)
    if not json_match:
        raise ValueError(f"Claude returned non-JSON response: {raw[:200]}")

    data = json.loads(json_match.group())

    return ContactDecision(
        channel=data["channel"],
        tone=data["tone"],
        send_time=data["send_time"],
        message=data["message"],
        reasoning=data.get("reasoning", ""),
    )
