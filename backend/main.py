from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api.routes.tenants import router as tenants_router
from api.routes.debtors import router as debtors_router
from api.routes.campaigns import router as campaigns_router
from api.routes.dashboard import router as dashboard_router
from api.routes.payments import router as payments_router, pay_router
from api.routes.webhooks import router as webhooks_router

app = FastAPI(
    title="QUESH API",
    description="B2C AI-powered debt collection platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenants_router, prefix="/api/v1")
app.include_router(debtors_router, prefix="/api/v1")
app.include_router(campaigns_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(payments_router)       # /p/{slug} redirect — no prefix
app.include_router(pay_router, prefix="/api/v1")
app.include_router(webhooks_router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
