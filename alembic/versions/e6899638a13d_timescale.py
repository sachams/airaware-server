"""init

Revision ID: e6899638a13d
Revises: 
Create Date: 2023-11-05 16:04:03.790761

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "e6899638a13d"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Timescale extension
    connection = op.get_bind()
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))


def downgrade() -> None:
    pass
