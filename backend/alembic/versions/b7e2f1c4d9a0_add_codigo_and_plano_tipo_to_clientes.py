"""add codigo and plano_tipo to clientes

Revision ID: b7e2f1c4d9a0
Revises: a5f1c2d3e4b6
Create Date: 2026-11-01 21:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7e2f1c4d9a0'
down_revision: Union[str, None] = 'a5f1c2d3e4b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Adiciona coluna plano_tipo com valor padrão 'mensal'
    op.add_column(
        'clientes',
        sa.Column('plano_tipo', sa.String(length=20), nullable=False, server_default='mensal'),
    )

    # 2. Adiciona coluna codigo como nullable temporariamente para backfill
    op.add_column(
        'clientes',
        sa.Column('codigo', sa.String(length=30), nullable=True),
    )

    # 3. Preenche código sequencial único nos registros existentes
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id FROM clientes ORDER BY criado_em ASC")).fetchall()
    for idx, r in enumerate(rows, 1):
        conn.execute(
            sa.text("UPDATE clientes SET codigo = :code WHERE id = :cid"),
            {"code": f"CLI-{idx:04d}", "cid": r[0]},
        )

    # 4. Altera codigo para NOT NULL e cria índice único
    # Em SQLite batch_alter_table é necessário, mas em PostgreSQL alter_column direto funciona.
    with op.batch_alter_table('clientes') as batch_op:
        batch_op.alter_column('codigo', existing_type=sa.String(length=30), nullable=False)
        batch_op.create_index('ix_clientes_codigo', ['codigo'], unique=True)


def downgrade() -> None:
    with op.batch_alter_table('clientes') as batch_op:
        batch_op.drop_index('ix_clientes_codigo')
        batch_op.drop_column('codigo')
        batch_op.drop_column('plano_tipo')
