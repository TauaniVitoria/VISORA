"""
Portal do Cliente: consultas somente leitura do próprio cliente autenticado (perfil CLIENTE).
O escopo (cliente + estacionamento) é derivado do usuário autenticado, nunca do request.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_cliente, get_db
from app.models.entities import Cliente, CobrancaStatus
from app.schemas.schemas import (
    CobrancaOut,
    PagamentoOut,
    PlanoOut,
    PortalAssinaturaOut,
    PortalMovimentacaoOut,
    PortalPerfilOut,
    PortalResumoOut,
    VeiculoOut,
)
from app.services.portal_service import PortalService

router = APIRouter(prefix="/portal", tags=["Portal do Cliente"])


@router.get("/me", response_model=PortalPerfilOut)
def portal_profile(cliente: Cliente = Depends(get_current_cliente), db: Session = Depends(get_db)) -> Any:
    """Dados cadastrais do cliente (documento mascarado) e seus veículos."""
    return PortalService.get_profile(db, cliente)


@router.get("/summary", response_model=PortalResumoOut)
def portal_summary(cliente: Cliente = Depends(get_current_cliente), db: Session = Depends(get_db)) -> Any:
    """Resumo: veículos no pátio agora, assinaturas ativas e cobranças pendentes."""
    return PortalService.get_summary(db, cliente)


@router.get("/vehicles", response_model=List[VeiculoOut])
def portal_vehicles(cliente: Cliente = Depends(get_current_cliente)) -> Any:
    return list(cliente.veiculos)


@router.get("/movements", response_model=List[PortalMovimentacaoOut])
def portal_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    cliente: Cliente = Depends(get_current_cliente),
    db: Session = Depends(get_db),
) -> Any:
    """Entradas, saídas e tempo de permanência dos veículos do cliente."""
    return PortalService.list_movements(db, cliente, skip=skip, limit=limit)


@router.get("/subscriptions", response_model=List[PortalAssinaturaOut])
def portal_subscriptions(cliente: Cliente = Depends(get_current_cliente), db: Session = Depends(get_db)) -> Any:
    return PortalService.list_subscriptions(db, cliente)


@router.get("/plans", response_model=List[PlanoOut])
def portal_plans(cliente: Cliente = Depends(get_current_cliente), db: Session = Depends(get_db)) -> Any:
    """Planos disponíveis no estacionamento do cliente."""
    return PortalService.list_plans(db, cliente)


@router.get("/charges", response_model=List[CobrancaOut])
def portal_charges(
    status_filter: Optional[CobrancaStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    cliente: Cliente = Depends(get_current_cliente),
    db: Session = Depends(get_db),
) -> Any:
    return PortalService.list_charges(db, cliente, status_filter=status_filter, skip=skip, limit=limit)


@router.get("/payments", response_model=List[PagamentoOut])
def portal_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    cliente: Cliente = Depends(get_current_cliente),
    db: Session = Depends(get_db),
) -> Any:
    return PortalService.list_payments(db, cliente, skip=skip, limit=limit)
