"""
Endpoints para gerenciamento de clientes e veículos.
Aplica isolamento multi-tenant por estacionamento_id.
"""

from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_tenant_id, get_db, require_roles
from app.models.entities import Cliente, UsuarioPerfil
from app.schemas.schemas import ClienteCreate, ClienteOut, VeiculoCreate, VeiculoOut
from app.services.business_services import CustomerVehicleService

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
        .options(selectinload(Cliente.veiculos))
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
        .options(selectinload(Cliente.veiculos))
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

