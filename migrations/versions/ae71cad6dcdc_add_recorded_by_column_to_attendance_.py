"""Add recorded_by column to attendance table

Revision ID: ae71cad6dcdc
Revises: 
Create Date: 2025-02-04 14:09:25.192746
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ae71cad6dcdc'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('attendance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('recorded_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_attendance_recorded_by_user',  # Add this constraint name
            'user',
            ['recorded_by'],
            ['id']
        )

def downgrade():
    with op.batch_alter_table('attendance', schema=None) as batch_op:
        batch_op.drop_constraint('fk_attendance_recorded_by_user', type_='foreignkey')
        batch_op.drop_column('recorded_by')
