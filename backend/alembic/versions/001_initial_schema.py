"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-12-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema with runs, molecules, and traces tables."""
    
    # Create runs table
    op.create_table(
        'runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('objective', sa.Text(), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('total_generated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_valid', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_passed', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        comment='Workflow execution runs'
    )
    
    # Create indexes for runs table
    op.create_index('idx_runs_status', 'runs', ['status'], unique=False)
    op.create_index('idx_runs_created', 'runs', ['created_at'], unique=False)
    
    # Create molecules table
    op.create_table(
        'molecules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('smiles', sa.String(length=500), nullable=False),
        sa.Column('smiles_canonical', sa.String(length=500), nullable=False),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('mw', sa.Float(), nullable=False),
        sa.Column('logp', sa.Float(), nullable=False),
        sa.Column('hbd', sa.Integer(), nullable=False),
        sa.Column('hba', sa.Integer(), nullable=False),
        sa.Column('tpsa', sa.Float(), nullable=False),
        sa.Column('rotatable_bonds', sa.Integer(), nullable=False),
        sa.Column('qed', sa.Float(), nullable=False),
        sa.Column('passed_screening', sa.Boolean(), nullable=False),
        sa.Column('num_violations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('violations', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('generation_method', sa.String(length=100), nullable=False),
        sa.Column('parent_smiles', sa.String(length=500), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id', 'smiles_canonical', name='uq_molecules_run_canonical'),
        comment='Generated molecules with properties'
    )
    
    # Create indexes for molecules table
    op.create_index('idx_molecules_run', 'molecules', ['run_id'], unique=False)
    op.create_index('idx_molecules_score', 'molecules', ['score'], unique=False)
    op.create_index('idx_molecules_qed', 'molecules', ['qed'], unique=False)
    op.create_index('idx_molecules_canonical', 'molecules', ['smiles_canonical'], unique=False)
    
    # Create traces table
    op.create_table(
        'traces',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('agent_type', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('timestamp', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Agent activity logs'
    )
    
    # Create indexes for traces table
    op.create_index('idx_traces_run', 'traces', ['run_id'], unique=False)
    op.create_index('idx_traces_round', 'traces', ['run_id', 'round_number'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('traces')
    op.drop_table('molecules')
    op.drop_table('runs')