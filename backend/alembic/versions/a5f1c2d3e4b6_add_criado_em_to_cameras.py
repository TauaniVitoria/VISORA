"""add criado_em to cameras

Revision ID: a5f1c2d3e4b6
Revises: 1e4940799eeb
Create Date: 2026-10-30 19:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a5f1c2d3e4b6'
down_revision: Union[str, None] = '1e4940799eeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default preenche linhas existentes; o default da aplicação segue valendo para novas linhas.
    op.add_column(
        'cameras',
        sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_column('cameras', 'criado_em')
