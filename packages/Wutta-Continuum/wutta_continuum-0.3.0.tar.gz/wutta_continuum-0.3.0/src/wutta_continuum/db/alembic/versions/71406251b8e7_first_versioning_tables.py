"""first versioning tables

Revision ID: 71406251b8e7
Revises:
Create Date: 2024-08-27 18:28:31.488291

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import wuttjamaican.db.util


# revision identifiers, used by Alembic.
revision: str = "71406251b8e7"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = ("wutta_continuum",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # transaction
    op.create_table(
        "transaction",
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("remote_addr", sa.String(length=50), nullable=True),
        sa.Column("user_id", wuttjamaican.db.util.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.uuid"], name=op.f("fk_transaction_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transaction")),
    )
    op.create_index(
        op.f("ix_transaction_user_id"), "transaction", ["user_id"], unique=False
    )

    # person
    op.create_table(
        "person_version",
        sa.Column(
            "uuid", wuttjamaican.db.util.UUID(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "full_name", sa.String(length=100), autoincrement=False, nullable=True
        ),
        sa.Column(
            "first_name", sa.String(length=50), autoincrement=False, nullable=True
        ),
        sa.Column(
            "middle_name", sa.String(length=50), autoincrement=False, nullable=True
        ),
        sa.Column(
            "last_name", sa.String(length=50), autoincrement=False, nullable=True
        ),
        sa.Column(
            "transaction_id", sa.BigInteger(), autoincrement=False, nullable=False
        ),
        sa.Column("end_transaction_id", sa.BigInteger(), nullable=True),
        sa.Column("operation_type", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint(
            "uuid", "transaction_id", name=op.f("pk_person_version")
        ),
    )
    op.create_index(
        op.f("ix_person_version_end_transaction_id"),
        "person_version",
        ["end_transaction_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_person_version_operation_type"),
        "person_version",
        ["operation_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_person_version_transaction_id"),
        "person_version",
        ["transaction_id"],
        unique=False,
    )

    # user
    op.create_table(
        "user_version",
        sa.Column(
            "uuid", wuttjamaican.db.util.UUID(), autoincrement=False, nullable=False
        ),
        sa.Column("username", sa.String(length=25), autoincrement=False, nullable=True),
        sa.Column("password", sa.String(length=60), autoincrement=False, nullable=True),
        sa.Column(
            "person_uuid",
            wuttjamaican.db.util.UUID(),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("active", sa.Boolean(), autoincrement=False, nullable=True),
        sa.Column(
            "transaction_id", sa.BigInteger(), autoincrement=False, nullable=False
        ),
        sa.Column("end_transaction_id", sa.BigInteger(), nullable=True),
        sa.Column("operation_type", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("uuid", "transaction_id", name=op.f("pk_user_version")),
    )
    op.create_index(
        op.f("ix_user_version_end_transaction_id"),
        "user_version",
        ["end_transaction_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_version_operation_type"),
        "user_version",
        ["operation_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_version_transaction_id"),
        "user_version",
        ["transaction_id"],
        unique=False,
    )

    # role
    op.create_table(
        "role_version",
        sa.Column(
            "uuid", wuttjamaican.db.util.UUID(), autoincrement=False, nullable=False
        ),
        sa.Column("name", sa.String(length=100), autoincrement=False, nullable=True),
        sa.Column("notes", sa.Text(), autoincrement=False, nullable=True),
        sa.Column(
            "transaction_id", sa.BigInteger(), autoincrement=False, nullable=False
        ),
        sa.Column("end_transaction_id", sa.BigInteger(), nullable=True),
        sa.Column("operation_type", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("uuid", "transaction_id", name=op.f("pk_role_version")),
    )
    op.create_index(
        op.f("ix_role_version_end_transaction_id"),
        "role_version",
        ["end_transaction_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_role_version_operation_type"),
        "role_version",
        ["operation_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_role_version_transaction_id"),
        "role_version",
        ["transaction_id"],
        unique=False,
    )

    # user_x_role
    op.create_table(
        "user_x_role_version",
        sa.Column(
            "uuid", wuttjamaican.db.util.UUID(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "user_uuid", wuttjamaican.db.util.UUID(), autoincrement=False, nullable=True
        ),
        sa.Column(
            "role_uuid", wuttjamaican.db.util.UUID(), autoincrement=False, nullable=True
        ),
        sa.Column(
            "transaction_id", sa.BigInteger(), autoincrement=False, nullable=False
        ),
        sa.Column("end_transaction_id", sa.BigInteger(), nullable=True),
        sa.Column("operation_type", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint(
            "uuid", "transaction_id", name=op.f("pk_user_x_role_version")
        ),
    )
    op.create_index(
        op.f("ix_user_x_role_version_end_transaction_id"),
        "user_x_role_version",
        ["end_transaction_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_x_role_version_operation_type"),
        "user_x_role_version",
        ["operation_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_x_role_version_transaction_id"),
        "user_x_role_version",
        ["transaction_id"],
        unique=False,
    )

    # permission
    op.create_table(
        "permission_version",
        sa.Column(
            "role_uuid",
            wuttjamaican.db.util.UUID(),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "permission", sa.String(length=254), autoincrement=False, nullable=False
        ),
        sa.Column(
            "transaction_id", sa.BigInteger(), autoincrement=False, nullable=False
        ),
        sa.Column("end_transaction_id", sa.BigInteger(), nullable=True),
        sa.Column("operation_type", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint(
            "role_uuid",
            "permission",
            "transaction_id",
            name=op.f("pk_permission_version"),
        ),
    )
    op.create_index(
        op.f("ix_permission_version_end_transaction_id"),
        "permission_version",
        ["end_transaction_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_permission_version_operation_type"),
        "permission_version",
        ["operation_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_permission_version_transaction_id"),
        "permission_version",
        ["transaction_id"],
        unique=False,
    )


def downgrade() -> None:

    # permission
    op.drop_index(
        op.f("ix_permission_version_transaction_id"), table_name="permission_version"
    )
    op.drop_index(
        op.f("ix_permission_version_operation_type"), table_name="permission_version"
    )
    op.drop_index(
        op.f("ix_permission_version_end_transaction_id"),
        table_name="permission_version",
    )
    op.drop_table("permission_version")

    # user_x_role
    op.drop_index(
        op.f("ix_user_x_role_version_transaction_id"), table_name="user_x_role_version"
    )
    op.drop_index(
        op.f("ix_user_x_role_version_operation_type"), table_name="user_x_role_version"
    )
    op.drop_index(
        op.f("ix_user_x_role_version_end_transaction_id"),
        table_name="user_x_role_version",
    )
    op.drop_table("user_x_role_version")

    # role
    op.drop_index(op.f("ix_role_version_transaction_id"), table_name="role_version")
    op.drop_index(op.f("ix_role_version_operation_type"), table_name="role_version")
    op.drop_index(op.f("ix_role_version_end_transaction_id"), table_name="role_version")
    op.drop_table("role_version")

    # user
    op.drop_index(op.f("ix_user_version_transaction_id"), table_name="user_version")
    op.drop_index(op.f("ix_user_version_operation_type"), table_name="user_version")
    op.drop_index(op.f("ix_user_version_end_transaction_id"), table_name="user_version")
    op.drop_table("user_version")

    # person
    op.drop_index(op.f("ix_person_version_transaction_id"), table_name="person_version")
    op.drop_index(op.f("ix_person_version_operation_type"), table_name="person_version")
    op.drop_index(
        op.f("ix_person_version_end_transaction_id"), table_name="person_version"
    )
    op.drop_table("person_version")

    # transaction
    op.drop_index(op.f("ix_transaction_user_id"), table_name="transaction")
    op.drop_table("transaction")
