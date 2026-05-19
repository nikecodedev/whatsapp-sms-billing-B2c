import re
import uuid
from io import BytesIO
from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.debtor import Debtor
from models.schemas import DebtorImportResult


COLUMN_MAP = {
    "nome_completo": ["nome_completo", "nome", "name", "devedor"],
    "cpf": ["cpf", "documento", "doc"],
    "telefone": ["telefone", "fone", "phone", "celular", "whatsapp"],
    "email": ["email", "e-mail", "e_mail"],
    "valor_divida": ["valor_divida", "valor", "divida", "debt", "amount"],
    "data_vencimento": ["data_vencimento", "vencimento", "due_date", "data"],
    "descricao": ["descricao", "descricão", "description", "produto"],
    "canal_preferencial": ["canal_preferencial", "canal", "channel"],
    "permite_parcelamento": ["permite_parcelamento", "parcelamento", "installment"],
    "observacoes": ["observacoes", "observações", "obs", "notes"],
}


def _normalize_cpf(raw: str) -> str:
    return re.sub(r"\D", "", str(raw))


def _normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", str(raw))
    if not digits.startswith("55"):
        digits = "55" + digits
    return "+" + digits


def _parse_decimal(raw) -> Decimal | None:
    try:
        cleaned = str(raw).replace("R$", "").replace(".", "").replace(",", ".").strip()
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _parse_date(raw) -> date | None:
    if isinstance(raw, date):
        return raw
    try:
        return pd.to_datetime(str(raw), dayfirst=True).date()
    except Exception:
        return None


def _map_columns(df: pd.DataFrame) -> dict[str, str]:
    """Return mapping from canonical name → actual column name in df."""
    lower_cols = {c.lower().strip(): c for c in df.columns}
    mapping = {}
    for canonical, aliases in COLUMN_MAP.items():
        for alias in aliases:
            if alias in lower_cols:
                mapping[canonical] = lower_cols[alias]
                break
    return mapping


async def import_debtors(
    file_content: bytes,
    filename: str,
    tenant_id: uuid.UUID,
    db: AsyncSession,
) -> DebtorImportResult:
    if filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_content))
    else:
        df = pd.read_excel(BytesIO(file_content))

    col_map = _map_columns(df)
    errors: list[str] = []
    imported = 0
    skipped = 0

    required = {"nome_completo", "cpf", "telefone", "valor_divida", "data_vencimento"}
    missing = required - col_map.keys()
    if missing:
        return DebtorImportResult(
            total=len(df),
            imported=0,
            skipped=len(df),
            errors=[f"Colunas obrigatórias não encontradas: {', '.join(missing)}"],
        )

    for idx, row in df.iterrows():
        row_num = idx + 2  # 1-based + header row

        nome = str(row.get(col_map["nome_completo"], "")).strip()
        cpf = _normalize_cpf(row.get(col_map["cpf"], ""))
        telefone = _normalize_phone(row.get(col_map["telefone"], ""))
        valor = _parse_decimal(row.get(col_map["valor_divida"], ""))
        vencimento = _parse_date(row.get(col_map["data_vencimento"], ""))

        if not nome or not cpf or not telefone:
            errors.append(f"Linha {row_num}: nome, CPF ou telefone ausente — ignorado")
            skipped += 1
            continue
        if len(cpf) != 11:
            errors.append(f"Linha {row_num}: CPF inválido ({cpf}) — ignorado")
            skipped += 1
            continue
        if valor is None or valor <= 0:
            errors.append(f"Linha {row_num}: valor_divida inválido — ignorado")
            skipped += 1
            continue
        if vencimento is None:
            errors.append(f"Linha {row_num}: data_vencimento inválida — ignorado")
            skipped += 1
            continue

        # Skip duplicates (same tenant + CPF)
        result = await db.execute(
            select(Debtor).where(Debtor.tenant_id == tenant_id, Debtor.cpf == cpf)
        )
        if result.scalar_one_or_none():
            skipped += 1
            continue

        debtor = Debtor(
            tenant_id=tenant_id,
            nome_completo=nome,
            cpf=cpf,
            telefone=telefone,
            email=str(row.get(col_map.get("email", ""), "")).strip() or None,
            valor_divida=valor,
            data_vencimento=vencimento,
            descricao=str(row.get(col_map.get("descricao", ""), "")).strip() or None,
            canal_preferencial=str(row.get(col_map.get("canal_preferencial", ""), "")).strip().lower() or None,
            permite_parcelamento=bool(row.get(col_map.get("permite_parcelamento", ""), False)),
            observacoes=str(row.get(col_map.get("observacoes", ""), "")).strip() or None,
        )
        db.add(debtor)
        imported += 1

    await db.commit()
    return DebtorImportResult(total=len(df), imported=imported, skipped=skipped, errors=errors)
