"""add catalog_updated_at to entries

Revision ID: 8d04d97b14ad
Revises: 90ded90a513a
Create Date: 2026-07-10 23:11:51.039373
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = '8d04d97b14ad'
down_revision = '90ded90a513a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Backfill from the existing `updated_at` for pre-existing rows: a
    # conservative assumption ("catalog was last touched whenever the row
    # was last touched at all") that never causes a false-negative skip of
    # a real catalog change - see core/models/entry.py for why this needs
    # to be a separate column at all.
    with op.batch_alter_table('entries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('catalog_updated_at', sa.DateTime(), nullable=True))

    conn = op.get_bind()
    conn.execute(sa.text("UPDATE entries SET catalog_updated_at = updated_at"))

    with op.batch_alter_table('entries', schema=None) as batch_op:
        batch_op.alter_column('catalog_updated_at', nullable=False)


def downgrade() -> None:
    with op.batch_alter_table('entries', schema=None) as batch_op:
        batch_op.drop_column('catalog_updated_at')
