"""Add state_reporter

Revision ID: 447438a85ef8
Revises: 10f209c14e18
Create Date: 2025-09-23 10:32:35.140390

"""

import json
import logging
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

from pyzenkit.utils import get_resource_path_fr

from mentat.const import PATH_RUN

# revision identifiers, used by Alembic.
revision = "447438a85ef8"
down_revision = "10f209c14e18"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")


def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, PermissionError):
        return None


def extract_severity_data(data):
    severities = ["info", "low", "medium", "high", "critical"]
    severity_timestamps = {s: [] for s in severities}

    for key, ts in data.items():
        for sev in severities:
            if f"_{sev}_" in key:
                severity_timestamps[sev].append(ts)
                break

    return severity_timestamps


def generate_sql(severity, ts):
    dt = datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"INSERT INTO state_reporter (last_successful_run, severity, createtime) VALUES ('{dt}', '{severity}', NOW());"
    )


def upgrade():
    op.create_table(
        "state_reporter",
        sa.Column("last_successful_run", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("createtime", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # https://github.com/sqlalchemy/alembic/issues/278#issuecomment-2484984520
    op.add_column(
        "state_reporter",
        sa.Column("severity", sa.Enum(name="event_class_severities", create_type=False), nullable=False),
    )

    # Add data from the pstate file, if it exists
    data = load_json(get_resource_path_fr(f"{PATH_RUN}/mentat-reporter.py.pstate"))
    if data:
        severity_data = extract_severity_data(data)
        for severity, timestamps in severity_data.items():
            op.execute(generate_sql(severity, max(timestamps)))
    else:
        logger.warning("pstate file not found or unreadable; state_reporter table will start empty.")


def downgrade():
    op.drop_table("state_reporter")
