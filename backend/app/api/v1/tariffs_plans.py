"""
Endpoints de tarifas avulsas, planos e assinaturas.
"""

from datetime import timedelta
from decimal import Decimal
from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant_id, get_db, require_roles
from app.models.entities import Assinatura, AssinaturaStatus, AssinaturaVeiculo, Plano, Tarifa, UsuarioPerfil, Veiculo
from app.schemas.schemas import AssinaturaCreate, AssinaturaOut, PlanoCreate, PlanoOut, TarifaCreate, TarifaOut
from app.services.business_services import TariffPlanService

router = APIRouter(prefix="/tariffs-plans", tags=["Tarifas e Planos"])


# --- Tarifas ---
@router.post(
    "/tariffs",
    response_model=TarifaOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def create_tariff(
    tariff_in: TarifaCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """Configura nova tarifa horária, adicional, diária e tempo de tolerância."""
    return TariffPlanService.create_tariff(db, tenant_id, tariff_in)


@router.get("/tariffs/active", response_model=TarifaOut)
def get_active_tariff(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """Retorna a tarifa vigente no estacionamento."""
    return TariffPlanService.get_active_tariff(db, tenant_id)


# --- Planos ---
@router.post(
    "/plans",
    response_model=PlanoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def create_plan(
    plan_in: PlanoCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """Cadastra plano de estacionamento (diário)."""
    return TariffPlanService.create_plan(db, tenant_id, plan_in)


@router.get("/plans", response_model=List[PlanoOut])
def list_plans(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """Lista todos os planos ativos do estacionamento."""
    stmt = select(Plano).where(Plano.estacionamento_id == tenant_id, Plano.ativo.is_(True))
    return list(db.scalars(stmt).all())


# --- Assinaturas ---
@router.post(
    "/subscriptions",
    response_model=AssinaturaOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)
def create_subscription(
    sub_in: AssinaturaCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> Any:
    """Contrata assinatura de um plano para um cliente e vincula veículos."""
    stmt_plan = select(Plano).where(Plano.id == sub_in.plano_id, Plano.estacionamento_id == tenant_id)
    plano = db.scalar(stmt_plan)
    if not plano:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano não encontrado.")

    # Calcula data_fim conforme recorrência
    d_inicio = sub_in.data_inicio
    d_fim = d_inicio + timedelta(days=30)

    # Cálculo do valor considerando veículos adicionais
    qtd_veiculos = len(sub_in.veiculos_ids)
    veiculos_extras = max(0, qtd_veiculos - plano.limite_veiculos)
    valor_extra = Decimal(str(veiculos_extras)) * plano.valor_veiculo_adicional
    valor_total = plano.valor_base + valor_extra

    assinatura = Assinatura(
        cliente_id=sub_in.cliente_id,
        plano_id=plano.id,
        estacionamento_id=tenant_id,
        data_inicio=d_inicio,
        data_fim=d_fim,
        status=AssinaturaStatus.ATIVA.value,
        valor_total=valor_total,
    )
    db.add(assinatura)
    db.flush()

    # Vincula os veículos à assinatura
    for v_id in sub_in.veiculos_ids:
        # Valida que o veículo existe, está ativo e pertence ao cliente da assinatura no mesmo estacionamento
        v_stmt = select(Veiculo).where(
            Veiculo.id == v_id,
            Veiculo.estacionamento_id == tenant_id,
            Veiculo.cliente_id == sub_in.cliente_id,
        )
        if not db.scalar(v_stmt):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Veículo {v_id} inválido ou não pertence ao cliente informado.",
            )
        av = AssinaturaVeiculo(assinatura_id=assinatura.id, veiculo_id=v_id)
        db.add(av)

    db.commit()
    db.refresh(assinatura)
    return assinatura

