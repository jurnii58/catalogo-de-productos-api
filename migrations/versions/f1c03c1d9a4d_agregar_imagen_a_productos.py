"""agregar imagen a productos

Revision ID: f1c03c1d9a4d
Revises: b66930f86f43
Create Date: 2026-11-13 20:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1c03c1d9a4d"
down_revision: Union[str, Sequence[str], None] = "b66930f86f43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("productos", sa.Column("imagen", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("productos", "imagen")
