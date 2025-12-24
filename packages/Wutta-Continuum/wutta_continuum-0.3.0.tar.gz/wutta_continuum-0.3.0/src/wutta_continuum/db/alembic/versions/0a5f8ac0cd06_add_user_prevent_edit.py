"""add user.prevent_edit

Revision ID: 0a5f8ac0cd06
Revises: 71406251b8e7
Create Date: 2024-11-24 17:39:57.415425

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0a5f8ac0cd06"
down_revision: Union[str, None] = "71406251b8e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # user
    op.add_column(
        "user_version",
        sa.Column("prevent_edit", sa.Boolean(), autoincrement=False, nullable=True),
    )


def downgrade() -> None:

    # user
    op.drop_column("user_version", "prevent_edit")
