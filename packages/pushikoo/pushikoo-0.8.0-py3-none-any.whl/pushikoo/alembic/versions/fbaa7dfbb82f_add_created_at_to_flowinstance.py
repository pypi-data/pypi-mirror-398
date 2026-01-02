"""add created_at to flowinstance

Revision ID: fbaa7dfbb82f
Revises: 626aa6a4605a
Create Date: 2025-12-19 13:52:36.203121

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fbaa7dfbb82f"
down_revision: Union[str, None] = "626aa6a4605a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite requires a default value when adding NOT NULL column to existing table
    with op.batch_alter_table("flowinstance", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("(datetime('now'))"),
            )
        )

    # Remove server_default after column is added
    with op.batch_alter_table("flowinstance", schema=None) as batch_op:
        batch_op.alter_column("created_at", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("flowinstance", schema=None) as batch_op:
        batch_op.drop_column("created_at")
