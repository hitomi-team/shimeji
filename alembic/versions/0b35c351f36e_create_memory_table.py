"""create memory table

Revision ID: 0b35c351f36e
Revises: 
Create Date: 2022-04-21 18:18:53.401740

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b35c351f36e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'memories',
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('author_id', sa.BigInteger(), nullable=False),
        sa.Column('author', sa.String(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('encoding_model', sa.String(), nullable=False),
        sa.Column('encoding', sa.String(), nullable=False),
    )
    op.create_index(op.f('ix_memories_created_at'), 'memories', ['created_at'], unique=False)
    op.create_index(op.f('ix_memories_author_id'), 'memories', ['author_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_memories_author_id'), table_name='memories')
    op.drop_index(op.f('ix_memories_created_at'), table_name='memories')
    op.drop_table('memories')
