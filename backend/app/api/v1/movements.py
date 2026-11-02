"""
Endpoints para controle de fluxo de veículos (Entrada, Saída, Histórico e Correções Manuais).
Suporta integração com câmeras ALPR e controle operacional de pátio.
"""

from datetime import datetime
from typing import Any, List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_tenant_id, get_current_user, get_db, require_roles
from app.models.entities import Movimentacao, MovimentacaoStatus, Usuario, UsuarioPerfil, Veiculo
from app.schemas.schemas import (
    MovimentacaoCorrecaoManual,
    MovimentacaoEntrada,
    MovimentacaoOut,
    MovimentacaoSaida,
)
from app.services.business_services import MovementService

router = APIRouter(prefix="/movements", tags=["Movimentações e ALPR"])


@router.post(
    "/entry",
    response_model=MovimentacaoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def register_entry(
    entry_in: MovimentacaoEntrada,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """
    Registra entrada de veículo.
    Identifica plano ativo, valida placa e previne duas entradas abertas para o mesmo veículo.
    """
    return MovementService.register_entry(db, tenant_id, entry_in)


@router.post(
    "/exit",
    response_model=MovimentacaoOut,
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def register_exit(
    exit_in: MovimentacaoSaida,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """
    Registra saída de veículo.
    Localiza entrada aberta, calcula permanência, aplica tarifa/plano e gera cobrança.
    """
    mov, cobranca = MovementService.register_exit(db, tenant_id, exit_in)
    return mov


@router.get(
    "/active",
    response_model=List[MovimentacaoOut],
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def list_active_vehicles(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """Lista todos os veículos atualmente estacionados (permanência aberta)."""
    stmt = (
        select(Movimentacao)
        .options(
            selectinload(Movimentacao.cobranca),
            selectinload(Movimentacao.veiculo).selectinload(Veiculo.cliente),
        )
        .where(
            Movimentacao.estacionamento_id == tenant_id,
            Movimentacao.status == MovimentacaoStatus.ABERTA.value,
        )
        .order_by(Movimentacao.entrada_em.desc())
    )
    return list(db.scalars(stmt).all())


@router.get(
    "/history",
    response_model=List[MovimentacaoOut],
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def list_movement_history(
    placa: Optional[str] = Query(None, description="Filtrar por placa do veículo"),
    status_filter: Optional[MovimentacaoStatus] = Query(None, description="Filtrar por status"),
    data_inicio: Optional[datetime] = Query(None, description="Data/hora inicial"),
    data_fim: Optional[datetime] = Query(None, description="Data/hora final"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """
    Histórico completo de entradas e saídas com suporte a filtros, paginação e ordenação.
    """
    stmt = (
        select(Movimentacao)
        .options(
            selectinload(Movimentacao.cobranca),
            selectinload(Movimentacao.veiculo).selectinload(Veiculo.cliente),
        )
        .where(Movimentacao.estacionamento_id == tenant_id)
    )

    if placa:
        stmt = stmt.where(Movimentacao.placa == placa.strip().upper().replace("-", ""))
    if status_filter:
        stmt = stmt.where(Movimentacao.status == status_filter.value)
    if data_inicio:
        stmt = stmt.where(Movimentacao.entrada_em >= data_inicio)
    if data_fim:
        stmt = stmt.where(Movimentacao.entrada_em <= data_fim)

    stmt = stmt.order_by(Movimentacao.entrada_em.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


@router.patch(
    "/{movimentacao_id}/correction",
    response_model=MovimentacaoOut,
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def manual_correction(
    movimentacao_id: uuid.UUID,
    correction: MovimentacaoCorrecaoManual,
    request: Request,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Realiza correção manual de placa ou status de uma movimentação com registro de auditoria.
    """
    ip = request.client.host if request.client else None
    return MovementService.manual_correction(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        movimentacao_id=movimentacao_id,
        correction=correction,
        ip_origem=ip,
    )

