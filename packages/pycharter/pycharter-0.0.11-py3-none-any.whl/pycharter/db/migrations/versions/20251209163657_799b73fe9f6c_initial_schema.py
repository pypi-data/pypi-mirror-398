"""Initial schema

Revision ID: 799b73fe9f6c
Revises: 
Create Date: 2025-12-09 16:36:57.351967

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '799b73fe9f6c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Create independent tables (no foreign key dependencies)
    op.create_table('owners',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('team', sa.String(length=255), nullable=True),
    sa.Column('additional_info', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email', name='uq_owners_email'),
    schema='pycharter'
    )
    op.create_table('domains',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('name', name='uq_domains_name'),
    schema='pycharter'
    )
    op.create_table('systems',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('app_id', sa.String(length=255), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('name', name='uq_systems_name'),
    schema='pycharter'
    )
    
    # Step 2: Create data_contracts table WITHOUT foreign keys to circular dependencies
    # (We'll add those foreign keys later after the referenced tables exist)
    op.create_table('data_contracts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('version', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('schema_id', sa.UUID(), nullable=True),
    sa.Column('coercion_rules_id', sa.UUID(), nullable=True),
    sa.Column('validation_rules_id', sa.UUID(), nullable=True),
    sa.Column('metadata_record_id', sa.UUID(), nullable=True),
    sa.Column('schema_version', sa.String(length=50), nullable=True),
    sa.Column('coercion_rules_version', sa.String(length=50), nullable=True),
    sa.Column('validation_rules_version', sa.String(length=50), nullable=True),
    sa.Column('metadata_version', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', sa.String(length=255), nullable=True),
    sa.Column('updated_by', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', 'version', name='uq_data_contracts_name_version'),
    schema='pycharter'
    )
    
    # Step 3: Create schemas (references data_contracts)
    op.create_table('schemas',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('data_contract_id', sa.UUID(), nullable=False),
    sa.Column('version', sa.String(length=50), nullable=False),
    sa.Column('schema_data', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['data_contract_id'], ['pycharter.data_contracts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('data_contract_id', 'version', name='uq_schemas_contract_version'),
    schema='pycharter'
    )
    
    # Step 4: Create coercion_rules and validation_rules (references data_contracts and schemas)
    op.create_table('coercion_rules',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('data_contract_id', sa.UUID(), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('version', sa.String(length=50), nullable=False),
    sa.Column('rules', sa.JSON(), nullable=False),
    sa.Column('schema_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['data_contract_id'], ['pycharter.data_contracts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['schema_id'], ['pycharter.schemas.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('data_contract_id', 'version', name='uq_coercion_rules_contract_version'),
    schema='pycharter'
    )
    op.create_table('validation_rules',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('data_contract_id', sa.UUID(), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('version', sa.String(length=50), nullable=False),
    sa.Column('rules', sa.JSON(), nullable=False),
    sa.Column('schema_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['data_contract_id'], ['pycharter.data_contracts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['schema_id'], ['pycharter.schemas.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('data_contract_id', 'version', name='uq_validation_rules_contract_version'),
    schema='pycharter'
    )
    
    # Step 5: Create metadata_records (references data_contracts)
    op.create_table('metadata_records',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('data_contract_id', sa.UUID(), nullable=False),
    sa.Column('version', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', sa.String(length=255), nullable=True),
    sa.Column('updated_by', sa.String(length=255), nullable=True),
    sa.Column('governance_rules', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['data_contract_id'], ['pycharter.data_contracts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('data_contract_id', 'version', name='uq_metadata_records_contract_version'),
    schema='pycharter'
    )
    
    # Step 6: Create metadata record association tables
    op.create_table('metadata_record_bu_sme',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('metadata_record_id', sa.UUID(), nullable=False),
    sa.Column('owner_id', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['metadata_record_id'], ['pycharter.metadata_records.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['owner_id'], ['pycharter.owners.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('metadata_record_id', 'owner_id', name='uq_mr_bu_sme'),
    schema='pycharter'
    )
    op.create_table('metadata_record_business_owners',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('metadata_record_id', sa.UUID(), nullable=False),
    sa.Column('owner_id', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['metadata_record_id'], ['pycharter.metadata_records.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['owner_id'], ['pycharter.owners.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('metadata_record_id', 'owner_id', name='uq_mr_business_owner'),
    schema='pycharter'
    )
    op.create_table('metadata_record_domains',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('metadata_record_id', sa.UUID(), nullable=False),
    sa.Column('domain_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['domain_id'], ['pycharter.domains.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['metadata_record_id'], ['pycharter.metadata_records.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('metadata_record_id', 'domain_id', name='uq_mr_domain'),
    schema='pycharter'
    )
    op.create_table('metadata_record_it_application_owners',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('metadata_record_id', sa.UUID(), nullable=False),
    sa.Column('owner_id', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['metadata_record_id'], ['pycharter.metadata_records.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['owner_id'], ['pycharter.owners.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('metadata_record_id', 'owner_id', name='uq_mr_it_application_owner'),
    schema='pycharter'
    )
    op.create_table('metadata_record_it_sme',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('metadata_record_id', sa.UUID(), nullable=False),
    sa.Column('owner_id', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['metadata_record_id'], ['pycharter.metadata_records.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['owner_id'], ['pycharter.owners.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('metadata_record_id', 'owner_id', name='uq_mr_it_sme'),
    schema='pycharter'
    )
    op.create_table('metadata_record_support_lead',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('metadata_record_id', sa.UUID(), nullable=False),
    sa.Column('owner_id', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['metadata_record_id'], ['pycharter.metadata_records.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['owner_id'], ['pycharter.owners.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('metadata_record_id', 'owner_id', name='uq_mr_support_lead'),
    schema='pycharter'
    )
    op.create_table('metadata_record_system_pulls',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('metadata_record_id', sa.UUID(), nullable=False),
    sa.Column('system_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['metadata_record_id'], ['pycharter.metadata_records.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['system_id'], ['pycharter.systems.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('metadata_record_id', 'system_id', name='uq_mr_system_pull'),
    schema='pycharter'
    )
    op.create_table('metadata_record_system_pushes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('metadata_record_id', sa.UUID(), nullable=False),
    sa.Column('system_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['metadata_record_id'], ['pycharter.metadata_records.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['system_id'], ['pycharter.systems.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('metadata_record_id', 'system_id', name='uq_mr_system_push'),
    schema='pycharter'
    )
    op.create_table('metadata_record_system_sources',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('metadata_record_id', sa.UUID(), nullable=False),
    sa.Column('system_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['metadata_record_id'], ['pycharter.metadata_records.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['system_id'], ['pycharter.systems.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('metadata_record_id', 'system_id', name='uq_mr_system_source'),
    schema='pycharter'
    )
    
    # Step 7: Add foreign keys from data_contracts to other tables (circular dependencies)
    # These are deferred because the referenced tables now exist
    op.create_foreign_key(
        'fk_data_contracts_schema_id',
        'data_contracts', 'schemas',
        ['schema_id'], ['id'],
        source_schema='pycharter', referent_schema='pycharter',
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_data_contracts_coercion_rules_id',
        'data_contracts', 'coercion_rules',
        ['coercion_rules_id'], ['id'],
        source_schema='pycharter', referent_schema='pycharter',
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_data_contracts_validation_rules_id',
        'data_contracts', 'validation_rules',
        ['validation_rules_id'], ['id'],
        source_schema='pycharter', referent_schema='pycharter',
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_data_contracts_metadata_record_id',
        'data_contracts', 'metadata_records',
        ['metadata_record_id'], ['id'],
        source_schema='pycharter', referent_schema='pycharter',
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop foreign keys first
    op.drop_constraint('fk_data_contracts_metadata_record_id', 'data_contracts', schema='pycharter', type_='foreignkey')
    op.drop_constraint('fk_data_contracts_validation_rules_id', 'data_contracts', schema='pycharter', type_='foreignkey')
    op.drop_constraint('fk_data_contracts_coercion_rules_id', 'data_contracts', schema='pycharter', type_='foreignkey')
    op.drop_constraint('fk_data_contracts_schema_id', 'data_contracts', schema='pycharter', type_='foreignkey')
    
    # Drop tables in reverse order
    op.drop_table('metadata_record_system_sources', schema='pycharter')
    op.drop_table('metadata_record_system_pushes', schema='pycharter')
    op.drop_table('metadata_record_system_pulls', schema='pycharter')
    op.drop_table('metadata_record_support_lead', schema='pycharter')
    op.drop_table('metadata_record_it_sme', schema='pycharter')
    op.drop_table('metadata_record_it_application_owners', schema='pycharter')
    op.drop_table('metadata_record_domains', schema='pycharter')
    op.drop_table('metadata_record_business_owners', schema='pycharter')
    op.drop_table('metadata_record_bu_sme', schema='pycharter')
    op.drop_table('validation_rules', schema='pycharter')
    op.drop_table('systems', schema='pycharter')
    op.drop_table('schemas', schema='pycharter')
    op.drop_table('owners', schema='pycharter')
    op.drop_table('metadata_records', schema='pycharter')
    op.drop_table('domains', schema='pycharter')
    op.drop_table('data_contracts', schema='pycharter')
    op.drop_table('coercion_rules', schema='pycharter')
