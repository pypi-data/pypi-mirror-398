"""drop time zones

Revision ID: b59a34266288
Revises: efdcb2c75034
Create Date: 2025-12-14 19:10:11.627188

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import wuttjamaican.db.util
from sqlalchemy.dialects import postgresql
from wuttjamaican.util import make_utc

# revision identifiers, used by Alembic.
revision: str = "b59a34266288"
down_revision: Union[str, None] = "efdcb2c75034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # upgrade.created
    op.add_column("upgrade", sa.Column("created_new", sa.DateTime(), nullable=True))
    upgrade = sa.sql.table(
        "upgrade",
        sa.sql.column("uuid"),
        sa.sql.column("created"),
        sa.sql.column("created_new"),
    )
    cursor = op.get_bind().execute(upgrade.select())
    for row in cursor.fetchall():
        op.get_bind().execute(
            upgrade.update()
            .where(upgrade.c.uuid == row.uuid)
            .values({"created_new": make_utc(row.created)})
        )
    op.drop_column("upgrade", "created")
    op.alter_column(
        "upgrade",
        "created_new",
        new_column_name="created",
        nullable=False,
        existing_type=sa.DateTime(),
        existing_nullable=True,
    )

    # upgrade.executed
    op.add_column("upgrade", sa.Column("executed_new", sa.DateTime(), nullable=True))
    upgrade = sa.sql.table(
        "upgrade",
        sa.sql.column("uuid"),
        sa.sql.column("executed"),
        sa.sql.column("executed_new"),
    )
    cursor = op.get_bind().execute(upgrade.select())
    for row in cursor.fetchall():
        if row.executed:
            op.get_bind().execute(
                upgrade.update()
                .where(upgrade.c.uuid == row.uuid)
                .values({"executed_new": make_utc(row.executed)})
            )
    op.drop_column("upgrade", "executed")
    op.alter_column(
        "upgrade",
        "executed_new",
        new_column_name="executed",
        existing_type=sa.DateTime(),
        existing_nullable=True,
    )

    # user_api_token.created
    op.add_column(
        "user_api_token", sa.Column("created_new", sa.DateTime(), nullable=True)
    )
    user_api_token = sa.sql.table(
        "user_api_token",
        sa.sql.column("uuid"),
        sa.sql.column("created"),
        sa.sql.column("created_new"),
    )
    cursor = op.get_bind().execute(user_api_token.select())
    for row in cursor.fetchall():
        op.get_bind().execute(
            user_api_token.update()
            .where(user_api_token.c.uuid == row.uuid)
            .values({"created_new": make_utc(row.created)})
        )
    op.drop_column("user_api_token", "created")
    op.alter_column(
        "user_api_token",
        "created_new",
        new_column_name="created",
        nullable=False,
        existing_type=sa.DateTime(),
        existing_nullable=True,
    )


def downgrade() -> None:

    # user_api_token.created
    op.add_column(
        "user_api_token",
        sa.Column("created_old", sa.DateTime(timezone=True), nullable=True),
    )
    user_api_token = sa.sql.table(
        "user_api_token",
        sa.sql.column("uuid"),
        sa.sql.column("created"),
        sa.sql.column("created_old"),
    )
    cursor = op.get_bind().execute(user_api_token.select())
    for row in cursor.fetchall():
        op.get_bind().execute(
            user_api_token.update()
            .where(user_api_token.c.uuid == row.uuid)
            .values({"created_old": row.created})
        )
    op.drop_column("user_api_token", "created")
    op.alter_column(
        "user_api_token",
        "created_old",
        new_column_name="created",
        nullable=False,
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
    )

    # upgrade.executed
    op.add_column(
        "upgrade", sa.Column("executed_old", sa.DateTime(timezone=True), nullable=True)
    )
    upgrade = sa.sql.table(
        "upgrade",
        sa.sql.column("uuid"),
        sa.sql.column("executed"),
        sa.sql.column("executed_old"),
    )
    cursor = op.get_bind().execute(upgrade.select())
    for row in cursor.fetchall():
        if row.executed:
            op.get_bind().execute(
                upgrade.update()
                .where(upgrade.c.uuid == row.uuid)
                .values({"executed_old": row.executed})
            )
    op.drop_column("upgrade", "executed")
    op.alter_column(
        "upgrade",
        "executed_old",
        new_column_name="executed",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
    )

    # upgrade.created
    op.add_column(
        "upgrade", sa.Column("created_old", sa.DateTime(timezone=True), nullable=True)
    )
    upgrade = sa.sql.table(
        "upgrade",
        sa.sql.column("uuid"),
        sa.sql.column("created"),
        sa.sql.column("created_old"),
    )
    cursor = op.get_bind().execute(upgrade.select())
    for row in cursor.fetchall():
        op.get_bind().execute(
            upgrade.update()
            .where(upgrade.c.uuid == row.uuid)
            .values({"created_old": row.created})
        )
    op.drop_column("upgrade", "created")
    op.alter_column(
        "upgrade",
        "created_old",
        new_column_name="created",
        nullable=False,
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
