"""
Endpoints para o Dashboard Administrativo do Estacionamento.
Exibe métricas consolidadas em tempo real: veículos estacionados, entradas, saídas, receita.
"""

from typing import Any
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant_id, get_db, require_roles
from app.models.entities import UsuarioPerfil
from app.schemas.schemas import DashboardMetricsOut
from app.services.business_services import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard Executivo"])


@router.get(
    "/metrics",
    response_model=DashboardMetricsOut,
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def get_dashboard_metrics(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """
    Retorna indicadores agregados do dia e status geral do estacionamento:
    - Veículos atualmente estacionados
    - Entradas e saídas de hoje
    - Total de clientes e veículos cadastrados
    - Assinaturas ativas
    - Receita total registrada e volume de cobranças pendentes
    """
    return DashboardService.get_metrics(db, tenant_id)

