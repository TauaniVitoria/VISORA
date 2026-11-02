"""discontinue mensal plan (migrate mensal -> diario)

Os clientes com plano_tipo 'mensal' e os planos com tipo_recorrencia 'mensal'
passam a ser 'diario'. Nenhum registro é excluído. Os IDs afetados são
guardados na tabela plano_mensal_backup para permitir o downgrade.

Revision ID: d4f9a2b8c1e3
Revises: c3d8e5f2a1b7
Create Date: 2026-11-02 14:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4f9a2b8c1e3'
down_revision: Union[str, None] = 'c3d8e5f2a1b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'plano_mensal_backup',
        sa.Column('tabela', sa.String(20), nullable=False),
        sa.Column('registro_id', sa.String(36), nullable=False),
        sa.PrimaryKeyConstraint('tabela', 'registro_id'),
    )
    op.execute(
        "INSERT INTO plano_mensal_backup (tabela, registro_id) "
        "SELECT 'clientes', CAST(id AS VARCHAR(36)) FROM clientes WHERE plano_tipo = 'mensal'"
    )
    op.execute(
        "INSERT INTO plano_mensal_backup (tabela, registro_id) "
        "SELECT 'planos', CAST(id AS VARCHAR(36)) FROM planos WHERE tipo_recorrencia = 'mensal'"
    )
    op.execute("UPDATE clientes SET plano_tipo = 'diario' WHERE plano_tipo = 'mensal'")
    op.execute("UPDATE planos SET tipo_recorrencia = 'diario' WHERE tipo_recorrencia = 'mensal'")


def downgrade() -> None:
    op.execute(
        "UPDATE clientes SET plano_tipo = 'mensal' WHERE CAST(id AS VARCHAR(36)) IN "
        "(SELECT registro_id FROM plano_mensal_backup WHERE tabela = 'clientes')"
    )
    op.execute(
        "UPDATE planos SET tipo_recorrencia = 'mensal' WHERE CAST(id AS VARCHAR(36)) IN "
        "(SELECT registro_id FROM plano_mensal_backup WHERE tabela = 'planos')"
    )
    op.drop_table('plano_mensal_backup')

