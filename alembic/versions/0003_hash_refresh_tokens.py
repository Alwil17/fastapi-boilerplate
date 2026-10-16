"""hash refresh tokens at rest, add token families

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-16

Existing plaintext tokens are hashed in place (so current sessions keep working)
and each becomes its own family.
"""

import hashlib
import uuid

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

refresh_tokens = sa.table(
    "refresh_tokens",
    sa.column("id", sa.Integer),
    sa.column("token", sa.String),
    sa.column("family_id", sa.String),
)


def upgrade() -> None:
    op.add_column("refresh_tokens", sa.Column("family_id", sa.String(32)))

    bind = op.get_bind()
    for row_id, token in bind.execute(
        sa.select(refresh_tokens.c.id, refresh_tokens.c.token)
    ).all():
        bind.execute(
            refresh_tokens.update()
            .where(refresh_tokens.c.id == row_id)
            .values(
                token=hashlib.sha256(token.encode("utf-8")).hexdigest(),
                family_id=uuid.uuid4().hex,
            )
        )

    op.drop_index("ix_refresh_tokens_token", table_name="refresh_tokens")
    op.alter_column(
        "refresh_tokens",
        "token",
        new_column_name="token_hash",
        type_=sa.String(64),
        nullable=False,
    )
    op.alter_column("refresh_tokens", "family_id", nullable=False)
    op.create_index(
        "ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True
    )
    op.create_index(
        "ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"], unique=False
    )


def downgrade() -> None:
    # Hashes cannot be turned back into tokens: drop sessions instead.
    op.execute("DELETE FROM refresh_tokens")
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.alter_column(
        "refresh_tokens",
        "token_hash",
        new_column_name="token",
        type_=sa.String(),
        nullable=True,
    )
    op.drop_column("refresh_tokens", "family_id")
    op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"], unique=True)
