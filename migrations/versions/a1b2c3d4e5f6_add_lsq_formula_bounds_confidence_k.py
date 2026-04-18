"""add lsq_model_formula, lsq_param_bounds_json, confidence_k to forecast_configs

Revision ID: a1b2c3d4e5f6
Revises: fc1d48576d6c
Create Date: 2026-04-18 20:36:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "fc1d48576d6c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("forecast_configs") as batch_op:
        batch_op.add_column(
            sa.Column("lsq_model_formula", sa.Text(), nullable=False, server_default="")
        )
        batch_op.add_column(
            sa.Column("lsq_param_bounds_json", sa.Text(), nullable=False, server_default="{}")
        )
        batch_op.add_column(
            sa.Column("confidence_k", sa.Float(), nullable=False, server_default="2.0")
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("forecast_configs") as batch_op:
        batch_op.drop_column("confidence_k")
        batch_op.drop_column("lsq_param_bounds_json")
        batch_op.drop_column("lsq_model_formula")
