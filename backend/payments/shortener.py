import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.short_url import ShortUrl
from core.config import settings


async def shorten(url: str, db: AsyncSession) -> str:
    """Create a short URL entry and return the redirect URL."""
    slug = secrets.token_urlsafe(8)[:8]

    # Ensure slug uniqueness
    while True:
        existing = await db.execute(select(ShortUrl).where(ShortUrl.slug == slug))
        if not existing.scalar_one_or_none():
            break
        slug = secrets.token_urlsafe(8)[:8]

    db.add(ShortUrl(slug=slug, destination=url))
    await db.commit()
    return f"{settings.APP_BASE_URL}/p/{slug}"


async def resolve(slug: str, db: AsyncSession) -> str | None:
    result = await db.execute(select(ShortUrl).where(ShortUrl.slug == slug))
    record = result.scalar_one_or_none()
    return record.destination if record else None
