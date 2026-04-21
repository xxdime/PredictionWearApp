"""drop degradation_direction from template_parameters and GPR fields from forecast_configs

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-04-21 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: str | Sequence[str] | None = "b3c4d5e6f7a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop degradation_direction from template_parameters.

    Also drops GPR fields from forecast_configs.
    """
    with op.batch_alter_table("template_parameters") as batch_op:
        batch_op.drop_column("degradation_direction")

    with op.batch_alter_table("forecast_configs") as batch_op:
        batch_op.drop_column("gpr_kernel_type")
        batch_op.drop_column("gpr_alpha")
        batch_op.drop_column("gpr_confidence_level")


def downgrade() -> None:
    """Restore dropped columns with their original defaults."""
    with op.batch_alter_table("forecast_configs") as batch_op:
        batch_op.add_column(
            sa.Column("gpr_confidence_level", sa.Float(), nullable=False, server_default="0.95")
        )
        batch_op.add_column(
            sa.Column("gpr_alpha", sa.Float(), nullable=False, server_default="1e-06")
        )
        batch_op.add_column(
            sa.Column(
                "gpr_kernel_type", sa.String(length=64), nullable=False, server_default="RBF"
            )
        )

    with op.batch_alter_table("template_parameters") as batch_op:
        batch_op.add_column(
            sa.Column(
                "degradation_direction",
                sa.String(length=32),
                nullable=False,
                server_default="decrease_to_critical",
            )
        )
