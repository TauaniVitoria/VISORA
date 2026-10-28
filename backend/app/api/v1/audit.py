"""
Endpoints de consulta de auditoria do sistema.
"""

from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant_id, get_db, require_roles
from app.models.entities import Auditoria, UsuarioPerfil
from app.schemas.schemas import AuditoriaOut

router = APIRouter(prefix="/audit", tags=["Auditoria"])


@router.get(
    "/",
    response_model=List[AuditoriaOut],
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """Lista eventos de auditoria registrados para o estacionamento."""
    stmt = (
        select(Auditoria)
        .where(Auditoria.estacionamento_id == tenant_id)
        .order_by(Auditoria.criado_em.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())

