"""drop lsq_model_type and lsq_poly_degree from forecast_configs

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-04-20 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop lsq_model_type and lsq_poly_degree columns; only formula-based fitting is used."""
    with op.batch_alter_table("forecast_configs") as batch_op:
        batch_op.drop_column("lsq_model_type")
        batch_op.drop_column("lsq_poly_degree")


def downgrade() -> None:
    """Restore lsq_model_type and lsq_poly_degree columns with sensible defaults."""
    with op.batch_alter_table("forecast_configs") as batch_op:
        batch_op.add_column(
            sa.Column(
                "lsq_poly_degree", sa.Integer(), nullable=False, server_default="1"
            )
        )
        batch_op.add_column(
            sa.Column(
                "lsq_model_type", sa.String(length=32), nullable=False, server_default="formula"
            )
        )
