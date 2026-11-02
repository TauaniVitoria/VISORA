"""add_performance_composite_indexes

Revision ID: e5a1b3c7d8f9
Revises: d4f9a2b8c1e3
Create Date: 2026-11-02 14:53:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e5a1b3c7d8f9"
down_revision: Union[str, None] = "d4f9a2b8c1e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_movimentacoes_tenant_status",
        "movimentacoes",
        ["estacionamento_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_movimentacoes_tenant_placa_status",
        "movimentacoes",
        ["estacionamento_id", "placa", "status"],
        unique=False,
    )
    op.create_index(
        "ix_movimentacoes_tenant_entrada",
        "movimentacoes",
        ["estacionamento_id", "entrada_em"],
        unique=False,
    )
    op.create_index(
        "ix_cobrancas_tenant_status",
        "cobrancas",
        ["estacionamento_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_cobrancas_tenant_status", table_name="cobrancas")
    op.drop_index("ix_movimentacoes_tenant_entrada", table_name="movimentacoes")
    op.drop_index("ix_movimentacoes_tenant_placa_status", table_name="movimentacoes")
    op.drop_index("ix_movimentacoes_tenant_status", table_name="movimentacoes")

