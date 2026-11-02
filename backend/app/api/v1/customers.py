"""
Endpoints para gerenciamento de clientes e veículos.
Aplica isolamento multi-tenant por estacionamento_id.
"""

from datetime import datetime
from typing import Any, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_tenant_id, get_current_user, get_db, require_roles
from app.models.entities import Cliente, Usuario, UsuarioPerfil
from app.schemas.schemas import (
    ClienteCreate,
    ClienteMovimentacaoOut,
    ClienteOut,
    PortalAccessCreate,
    UsuarioOut,
    VeiculoCreate,
    VeiculoOut,
)
from app.services.business_services import CustomerVehicleService
from app.services.portal_service import PortalAccessService

router = APIRouter(prefix="/customers", tags=["Clientes e Veículos"])


@router.post(
    "/",
    response_model=ClienteOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def create_customer(
    customer_in: ClienteCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """
    Cadastra cliente exigindo pelo menos um veículo inicial associado.
    Garante que a placa seja única no estacionamento.
    """
    return CustomerVehicleService.create_customer_with_vehicles(db, tenant_id, customer_in)


@router.get(
    "/",
    response_model=List[ClienteOut],
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def list_customers(
    skip: int = 0,
    limit: int = 100,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """Lista clientes do estacionamento com seus respectivos veículos."""
    stmt = (
        select(Cliente)
        .options(selectinload(Cliente.veiculos), selectinload(Cliente.usuario))
        .where(Cliente.estacionamento_id == tenant_id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


@router.get(
    "/{client_id}",
    response_model=ClienteOut,
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def get_customer(
    client_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """Consulta dados de um cliente e seus veículos cadastrados."""
    stmt = (
        select(Cliente)
        .options(selectinload(Cliente.veiculos), selectinload(Cliente.usuario))
        .where(Cliente.id == client_id, Cliente.estacionamento_id == tenant_id)
    )
    cliente = db.scalar(stmt)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
    return cliente


@router.post(
    "/{client_id}/vehicles",
    response_model=VeiculoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def add_vehicle_to_customer(
    client_id: uuid.UUID,
    vehicle_in: VeiculoCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """Vincula um veículo adicional a um cliente existente."""
    return CustomerVehicleService.add_vehicle(db, tenant_id, client_id, vehicle_in)


@router.post(
    "/{client_id}/portal-access",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def create_portal_access(
    client_id: uuid.UUID,
    access_in: PortalAccessCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Cria o login do cliente no portal, com senha provisória informada pelo administrador."""
    return PortalAccessService.create_access(db, tenant_id, client_id, access_in, actor_id=current_user.id)


@router.delete(
    "/{client_id}/portal-access",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def revoke_portal_access(
    client_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Desativa o login do cliente no portal."""
    PortalAccessService.revoke_access(db, tenant_id, client_id, actor_id=current_user.id)


@router.get(
    "/{client_id}/movements",
    response_model=List[ClienteMovimentacaoOut],
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def get_customer_movements(
    client_id: uuid.UUID,
    placa: Optional[str] = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """Retorna histórico completo de movimentações de todos os veículos vinculados ao cliente."""
    return CustomerVehicleService.get_customer_movements(
        db=db,
        tenant_id=tenant_id,
        cliente_id=client_id,
        placa=placa,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )
