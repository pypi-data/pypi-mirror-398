"""Rename PipExtraIndexUrl to PipIndex.

Revision ID: c3e7f9a1b2d4
Revises: 375e5d19af3c
Create Date: 2025-12-16 00:45:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c3e7f9a1b2d4"
down_revision: Union[str, None] = "375e5d19af3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename the table
    op.rename_table("pipextraindexurl", "pipindex")

    # Drop old unique constraint and create new one
    # SQLite doesn't support renaming constraints directly, so we need to recreate
    with op.batch_alter_table("pipindex", schema=None) as batch_op:
        batch_op.drop_constraint("uix_pip_extra_index_url", type_="unique")
        batch_op.create_unique_constraint("uix_pip_index", ["url"])


def downgrade() -> None:
    """Downgrade schema."""
    # Rename the table back
    op.rename_table("pipindex", "pipextraindexurl")

    # Restore old constraint
    with op.batch_alter_table("pipextraindexurl", schema=None) as batch_op:
        batch_op.drop_constraint("uix_pip_index", type_="unique")
        batch_op.create_unique_constraint("uix_pip_extra_index_url", ["url"])
