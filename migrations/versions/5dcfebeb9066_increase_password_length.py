"""increase_password_length

Revision ID: 5dcfebeb9066
Revises: 328a95832fc2
Create Date: 2025-09-30 14:47:44.579077

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5dcfebeb9066'
down_revision = '328a95832fc2'
branch_labels = None
depends_on = None


def upgrade():
    # Increase password column length to accommodate longer scrypt hashes
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password',
                              existing_type=sa.VARCHAR(length=128),
                              type_=sa.String(length=255),
                              existing_nullable=False)


def downgrade():
    # Revert password column length back to original
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password',
                              existing_type=sa.String(length=255),
                              type_=sa.VARCHAR(length=128),
                              existing_nullable=False)
