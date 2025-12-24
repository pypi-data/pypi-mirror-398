"""add transaction_meta

Revision ID: 46fb4711411d
Revises: 989392cc191d
Create Date: 2025-12-18 21:22:33.382628

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import wuttjamaican.db.util


# revision identifiers, used by Alembic.
revision: str = "46fb4711411d"
down_revision: Union[str, None] = "989392cc191d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # transaction_meta
    op.create_table(
        "transaction_meta",
        sa.Column("transaction_id", sa.BigInteger(), nullable=False),
        sa.Column("key", sa.Unicode(length=255), nullable=False),
        sa.Column("value", sa.UnicodeText(), nullable=True),
        sa.PrimaryKeyConstraint(
            "transaction_id", "key", name=op.f("pk_transaction_meta")
        ),
    )


def downgrade() -> None:

    # transaction_meta
    op.drop_table("transaction_meta")
