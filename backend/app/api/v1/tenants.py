"""
Endpoints de gestão de Estacionamentos (Tenants).
Acesso restrito a administradores SaaS ou consulta do próprio tenant.
"""

from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.entities import Estacionamento, Usuario, UsuarioPerfil
from app.schemas.schemas import EstacionamentoCreate, EstacionamentoOut
from app.services.business_services import TenantService

router = APIRouter(prefix="/tenants", tags=["Tenants / Estacionamentos"])


@router.post(
    "/",
    response_model=EstacionamentoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UsuarioPerfil.SAAS_ADMIN))],
)
def create_tenant(tenant_in: EstacionamentoCreate, db: Session = Depends(get_db)) -> Any:
    """Cadastra um novo estacionamento na plataforma (SaaS Admin)."""
    return TenantService.create_parking(db, tenant_in)


@router.get(
    "/",
    response_model=List[EstacionamentoOut],
    dependencies=[Depends(require_roles(UsuarioPerfil.SAAS_ADMIN))],
)
def list_tenants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> Any:
    """Lista todos os estacionamentos cadastrados (SaaS Admin)."""
    return TenantService.list_parkings(db, skip=skip, limit=limit)


@router.get("/{tenant_id}", response_model=EstacionamentoOut)
def get_tenant(
    tenant_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Consulta detalhes de um estacionamento."""
    if (
        current_user.perfil != UsuarioPerfil.SAAS_ADMIN.value
        and current_user.estacionamento_id != tenant_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso não autorizado aos dados deste estacionamento.",
        )

    stmt = select(Estacionamento).where(Estacionamento.id == tenant_id)
    parking = db.scalar(stmt)
    if not parking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estacionamento não encontrado.")
    return parking

