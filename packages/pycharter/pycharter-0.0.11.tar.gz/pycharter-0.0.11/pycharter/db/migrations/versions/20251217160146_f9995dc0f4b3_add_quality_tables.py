"""Add quality tables

Revision ID: f9995dc0f4b3
Revises: ae0efda02aa1
Create Date: 2025-12-17 16:01:46.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f9995dc0f4b3'
down_revision: Union[str, None] = 'ae0efda02aa1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create quality_metrics table
    op.create_table(
        'quality_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('schema_id', sa.String(length=255), nullable=False),
        sa.Column('schema_version', sa.String(length=50), nullable=True),
        sa.Column('data_contract_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('violation_rate', sa.Float(), nullable=False),
        sa.Column('completeness', sa.Float(), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=False),
        sa.Column('record_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('valid_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('invalid_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('violation_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('field_scores', postgresql.JSON(), nullable=True),
        sa.Column('threshold_breaches', postgresql.JSON(), nullable=True),
        sa.Column('passed', sa.String(length=10), nullable=False, server_default='true'),
        sa.Column('check_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('additional_metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['data_contract_id'], ['pycharter.data_contracts.id'], ondelete='SET NULL'),
        schema='pycharter'
    )
    
    # Create indexes for quality_metrics
    op.create_index('ix_quality_metrics_schema_id', 'quality_metrics', ['schema_id'], schema='pycharter')
    op.create_index('ix_quality_metrics_data_contract_id', 'quality_metrics', ['data_contract_id'], schema='pycharter')
    op.create_index('ix_quality_metrics_check_timestamp', 'quality_metrics', ['check_timestamp'], schema='pycharter')
    
    # Create quality_violations table
    op.create_table(
        'quality_violations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('schema_id', sa.String(length=255), nullable=False),
        sa.Column('schema_version', sa.String(length=50), nullable=True),
        sa.Column('data_contract_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('record_identifier', sa.String(length=255), nullable=True),
        sa.Column('record_data', postgresql.JSON(), nullable=True),
        sa.Column('field_name', sa.String(length=255), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='warning'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(length=255), nullable=True),
        sa.Column('check_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('additional_metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['data_contract_id'], ['pycharter.data_contracts.id'], ondelete='SET NULL'),
        schema='pycharter'
    )
    
    # Create indexes for quality_violations
    op.create_index('ix_quality_violations_schema_id', 'quality_violations', ['schema_id'], schema='pycharter')
    op.create_index('ix_quality_violations_data_contract_id', 'quality_violations', ['data_contract_id'], schema='pycharter')
    op.create_index('ix_quality_violations_record_identifier', 'quality_violations', ['record_identifier'], schema='pycharter')
    op.create_index('ix_quality_violations_field_name', 'quality_violations', ['field_name'], schema='pycharter')
    op.create_index('ix_quality_violations_error_type', 'quality_violations', ['error_type'], schema='pycharter')
    op.create_index('ix_quality_violations_severity', 'quality_violations', ['severity'], schema='pycharter')
    op.create_index('ix_quality_violations_status', 'quality_violations', ['status'], schema='pycharter')
    op.create_index('ix_quality_violations_check_timestamp', 'quality_violations', ['check_timestamp'], schema='pycharter')


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_quality_violations_check_timestamp', table_name='quality_violations', schema='pycharter')
    op.drop_index('ix_quality_violations_status', table_name='quality_violations', schema='pycharter')
    op.drop_index('ix_quality_violations_severity', table_name='quality_violations', schema='pycharter')
    op.drop_index('ix_quality_violations_error_type', table_name='quality_violations', schema='pycharter')
    op.drop_index('ix_quality_violations_field_name', table_name='quality_violations', schema='pycharter')
    op.drop_index('ix_quality_violations_record_identifier', table_name='quality_violations', schema='pycharter')
    op.drop_index('ix_quality_violations_data_contract_id', table_name='quality_violations', schema='pycharter')
    op.drop_index('ix_quality_violations_schema_id', table_name='quality_violations', schema='pycharter')
    
    op.drop_index('ix_quality_metrics_check_timestamp', table_name='quality_metrics', schema='pycharter')
    op.drop_index('ix_quality_metrics_data_contract_id', table_name='quality_metrics', schema='pycharter')
    op.drop_index('ix_quality_metrics_schema_id', table_name='quality_metrics', schema='pycharter')
    
    # Drop tables
    op.drop_table('quality_violations', schema='pycharter')
    op.drop_table('quality_metrics', schema='pycharter')

