"""add event class priority

Revision ID: 10f209c14e18
Revises: 3306d4eb1032
Create Date: 2025-08-29 11:57:02.420436

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "10f209c14e18"
down_revision = "3306d4eb1032"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("event_classes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("priority", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    with op.batch_alter_table("event_classes", schema=None) as batch_op:
        batch_op.drop_column("priority")
