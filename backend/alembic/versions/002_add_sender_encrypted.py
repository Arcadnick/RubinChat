"""Add sender_encrypted_payload and sender_nonce for sender to see own messages

Revision ID: 002_sender_enc
Revises: 001_initial
Create Date: 2025-01-01 00:01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_sender_enc"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # nullable: existing messages have no sender copy (sender will see [sent] for those)
    op.add_column("messages", sa.Column("sender_encrypted_payload", sa.Text(), nullable=True))
    op.add_column("messages", sa.Column("sender_nonce", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "sender_nonce")
    op.drop_column("messages", "sender_encrypted_payload")
