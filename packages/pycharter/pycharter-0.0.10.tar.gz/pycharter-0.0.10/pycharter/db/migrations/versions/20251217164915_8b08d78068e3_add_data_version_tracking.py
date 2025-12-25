"""Add data version tracking to quality_metrics

Revision ID: 8b08d78068e3
Revises: f9995dc0f4b3
Create Date: 2025-12-17 16:49:15.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8b08d78068e3'
down_revision: Union[str, None] = 'f9995dc0f4b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add data version tracking columns to quality_metrics
    op.add_column(
        'quality_metrics',
        sa.Column('data_version', sa.String(length=255), nullable=True),
        schema='pycharter'
    )
    op.add_column(
        'quality_metrics',
        sa.Column('data_source', sa.String(length=500), nullable=True),
        schema='pycharter'
    )
    op.add_column(
        'quality_metrics',
        sa.Column('data_fingerprint', sa.String(length=64), nullable=True),
        schema='pycharter'
    )
    
    # Create indexes for new columns
    op.create_index(
        'ix_quality_metrics_data_version',
        'quality_metrics',
        ['data_version'],
        schema='pycharter'
    )
    op.create_index(
        'ix_quality_metrics_data_fingerprint',
        'quality_metrics',
        ['data_fingerprint'],
        schema='pycharter'
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_quality_metrics_data_fingerprint', table_name='quality_metrics', schema='pycharter')
    op.drop_index('ix_quality_metrics_data_version', table_name='quality_metrics', schema='pycharter')
    
    # Drop columns
    op.drop_column('quality_metrics', 'data_fingerprint', schema='pycharter')
    op.drop_column('quality_metrics', 'data_source', schema='pycharter')
    op.drop_column('quality_metrics', 'data_version', schema='pycharter')

