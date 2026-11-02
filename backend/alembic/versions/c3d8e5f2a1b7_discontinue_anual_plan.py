"""discontinue anual plan (migrate anual -> mensal)

Os clientes com plano_tipo 'anual' e os planos com tipo_recorrencia 'anual'
passam a ser 'mensal'. Nenhum registro é excluído. Os IDs afetados são
guardados na tabela plano_anual_backup para permitir o downgrade.

Revision ID: c3d8e5f2a1b7
Revises: b7e2f1c4d9a0
Create Date: 2026-11-02 13:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d8e5f2a1b7'
down_revision: Union[str, None] = 'b7e2f1c4d9a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'plano_anual_backup',
        sa.Column('tabela', sa.String(20), nullable=False),
        sa.Column('registro_id', sa.String(36), nullable=False),
        sa.PrimaryKeyConstraint('tabela', 'registro_id'),
    )
    op.execute(
        "INSERT INTO plano_anual_backup (tabela, registro_id) "
        "SELECT 'clientes', CAST(id AS VARCHAR(36)) FROM clientes WHERE plano_tipo = 'anual'"
    )
    op.execute(
        "INSERT INTO plano_anual_backup (tabela, registro_id) "
        "SELECT 'planos', CAST(id AS VARCHAR(36)) FROM planos WHERE tipo_recorrencia = 'anual'"
    )
    op.execute("UPDATE clientes SET plano_tipo = 'mensal' WHERE plano_tipo = 'anual'")
    op.execute("UPDATE planos SET tipo_recorrencia = 'mensal' WHERE tipo_recorrencia = 'anual'")


def downgrade() -> None:
    op.execute(
        "UPDATE clientes SET plano_tipo = 'anual' WHERE CAST(id AS VARCHAR(36)) IN "
        "(SELECT registro_id FROM plano_anual_backup WHERE tabela = 'clientes')"
    )
    op.execute(
        "UPDATE planos SET tipo_recorrencia = 'anual' WHERE CAST(id AS VARCHAR(36)) IN "
        "(SELECT registro_id FROM plano_anual_backup WHERE tabela = 'planos')"
    )
    op.drop_table('plano_anual_backup')

