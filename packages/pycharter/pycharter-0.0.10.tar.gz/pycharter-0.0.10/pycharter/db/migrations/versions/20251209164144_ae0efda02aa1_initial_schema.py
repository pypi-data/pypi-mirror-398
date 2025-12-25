"""Initial schema

Revision ID: ae0efda02aa1
Revises: 799b73fe9f6c
Create Date: 2025-12-09 16:41:44.279844

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae0efda02aa1'
down_revision: Union[str, None] = '799b73fe9f6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Empty migration - no changes needed
    pass


def downgrade() -> None:
    # Empty migration - no changes needed
    pass



