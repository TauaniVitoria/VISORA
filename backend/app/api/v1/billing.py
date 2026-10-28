"""
Endpoints de cobranças e pagamentos.
"""

from typing import Any, List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant_id, get_current_user, get_db, require_roles
from app.models.entities import Cobranca, CobrancaStatus, Pagamento, Usuario, UsuarioPerfil
from app.schemas.schemas import CobrancaOut, PagamentoCreate, PagamentoOut
from app.services.business_services import BillingPaymentService

router = APIRouter(prefix="/billing", tags=["Cobranças e Pagamentos"])


@router.get(
    "/charges",
    response_model=List[CobrancaOut],
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def list_charges(
    status_filter: Optional[CobrancaStatus] = Query(None, description="Filtrar por status da cobrança"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """Lista todas as cobranças emitidas no estacionamento com paginação."""
    stmt = select(Cobranca).where(Cobranca.estacionamento_id == tenant_id)
    if status_filter:
        stmt = stmt.where(Cobranca.status == status_filter.value)
    stmt = stmt.order_by(Cobranca.criado_em.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


@router.post(
    "/payments",
    response_model=PagamentoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def register_payment(
    payment_in: PagamentoCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Registra pagamento manual de uma cobrança (Pix, Dinheiro, Cartão, Boleto)."""
    return BillingPaymentService.register_payment(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        payment_in=payment_in,
    )

