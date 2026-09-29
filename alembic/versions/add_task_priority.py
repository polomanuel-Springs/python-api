import sqlalchemy as sa

from alembic import op

revision = "0002_task_priority"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tasks") as batch:
        batch.add_column(
            sa.Column(
                "priority",
                sa.Enum("low", "medium", "high", name="priority", native_enum=False),
                nullable=False,
                server_default="medium",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch:
        batch.drop_column("priority")
