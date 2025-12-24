"""remove password

Revision ID: 989392cc191d
Revises: 0a5f8ac0cd06
Create Date: 2025-10-29 19:42:52.985167

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import wuttjamaican.db.util


# revision identifiers, used by Alembic.
revision: str = "989392cc191d"
down_revision: Union[str, None] = "0a5f8ac0cd06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # user
    op.drop_column("user_version", "password")


def downgrade() -> None:

    # user
    op.add_column(
        "user_version",
        sa.Column(
            "password", sa.VARCHAR(length=60), autoincrement=False, nullable=True
        ),
    )
