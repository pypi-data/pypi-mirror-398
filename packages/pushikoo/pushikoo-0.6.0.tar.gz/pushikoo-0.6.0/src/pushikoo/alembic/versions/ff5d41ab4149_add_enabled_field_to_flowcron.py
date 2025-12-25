"""add_enabled_field_to_flowcron

Revision ID: ff5d41ab4149
Revises: fbaa7dfbb82f
Create Date: 2025-12-19 17:16:20.849666

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ff5d41ab4149"
down_revision: Union[str, None] = "fbaa7dfbb82f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("flowcron", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")
            )
        )

    with op.batch_alter_table("flowcron", schema=None) as batch_op:
        batch_op.alter_column("enabled", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("flowcron", schema=None) as batch_op:
        batch_op.drop_column("enabled")
