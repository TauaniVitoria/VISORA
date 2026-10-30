"""
Agregação das rotas da API v1.
"""

from fastapi import APIRouter

from app.api.v1.alpr import router as alpr_router
from app.api.v1.audit import router as audit_router
from app.api.v1.auth import router as auth_router
from app.api.v1.billing import router as billing_router
from app.api.v1.cameras import router as cameras_router
from app.api.v1.customers import router as customers_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.movements import router as movements_router
from app.api.v1.tariffs_plans import router as tariffs_plans_router
from app.api.v1.tenants import router as tenants_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(tenants_router)
api_router.include_router(customers_router)
api_router.include_router(cameras_router)
api_router.include_router(tariffs_plans_router)
api_router.include_router(movements_router)
api_router.include_router(billing_router)
api_router.include_router(dashboard_router)
api_router.include_router(audit_router)
api_router.include_router(alpr_router)

