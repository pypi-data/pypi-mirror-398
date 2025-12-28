from __future__ import annotations

import json
import random
from collections.abc import Sequence
from typing import Any, cast

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    WRITES_IDX_MAP,
    BaseCheckpointSaver,
    ChannelVersions,
    get_checkpoint_id,
)
from langgraph.checkpoint.serde.types import TASKS

MetadataInput = dict[str, Any] | None

"""
To add a new migration, add a new string to the MIGRATIONS list.
The position of the migration in the list is the version number.
"""
MIGRATIONS = [
    """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'checkpoint_migrations')
    CREATE TABLE checkpoint_migrations (
        v INTEGER PRIMARY KEY
    );""",
    """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'checkpoints')
    CREATE TABLE checkpoints (
        thread_id NVARCHAR(450) NOT NULL,
        checkpoint_ns NVARCHAR(450) NOT NULL DEFAULT '',
        checkpoint_id NVARCHAR(450) NOT NULL,
        parent_checkpoint_id NVARCHAR(450),
        [type] NVARCHAR(450),
        [checkpoint] NVARCHAR(MAX) NOT NULL,
        metadata NVARCHAR(MAX) NOT NULL DEFAULT '{}',
        PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
    );""",
    """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'checkpoint_blobs')
    CREATE TABLE checkpoint_blobs (
        thread_id NVARCHAR(450) NOT NULL,
        checkpoint_ns NVARCHAR(450) NOT NULL DEFAULT '',
        channel NVARCHAR(450) NOT NULL,
        version NVARCHAR(450) NOT NULL,
        [type] NVARCHAR(450) NOT NULL,
        blob VARBINARY(MAX),
        PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
    );""",
    """IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'checkpoint_writes')
    CREATE TABLE checkpoint_writes (
        thread_id NVARCHAR(450) NOT NULL,
        checkpoint_ns NVARCHAR(450) NOT NULL DEFAULT '',
        checkpoint_id NVARCHAR(450) NOT NULL,
        task_id NVARCHAR(450) NOT NULL,
        idx INTEGER NOT NULL,
        channel NVARCHAR(450) NOT NULL,
        [type] NVARCHAR(450),
        blob VARBINARY(MAX) NOT NULL,
        task_path NVARCHAR(450) NOT NULL DEFAULT '',
        PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
    );""",
    # Index migrations
    """IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'ix_checkpoints_thread_id')
    CREATE INDEX ix_checkpoints_thread_id ON checkpoints(thread_id);""",
    """IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'ix_checkpoint_blobs_thread_id')
    CREATE INDEX ix_checkpoint_blobs_thread_id ON checkpoint_blobs(thread_id);""",
    """IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'ix_checkpoint_writes_thread_id')
    CREATE INDEX ix_checkpoint_writes_thread_id ON checkpoint_writes(thread_id);""",
]

UPSERT_CHECKPOINT_BLOBS_SQL = """
    MERGE checkpoint_blobs AS target
    USING (SELECT ? AS thread_id, ? AS checkpoint_ns, ? AS channel,
                  ? AS version, ? AS [type], ? AS blob) AS source
    ON target.thread_id = source.thread_id
       AND target.checkpoint_ns = source.checkpoint_ns
       AND target.channel = source.channel
       AND target.version = source.version
    WHEN NOT MATCHED THEN
        INSERT (thread_id, checkpoint_ns, channel, version, [type], blob)
        VALUES (source.thread_id, source.checkpoint_ns, source.channel,
                source.version, source.[type], source.blob);
"""

UPSERT_CHECKPOINTS_SQL = """
    MERGE checkpoints AS target
    USING (SELECT ? AS thread_id, ? AS checkpoint_ns, ? AS checkpoint_id,
                  ? AS parent_checkpoint_id, ? AS [checkpoint], ? AS metadata) AS source
    ON target.thread_id = source.thread_id
       AND target.checkpoint_ns = source.checkpoint_ns
       AND target.checkpoint_id = source.checkpoint_id
    WHEN MATCHED THEN
        UPDATE SET [checkpoint] = source.[checkpoint], metadata = source.metadata
    WHEN NOT MATCHED THEN
        INSERT (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id,
                [checkpoint], metadata)
        VALUES (source.thread_id, source.checkpoint_ns, source.checkpoint_id,
                source.parent_checkpoint_id, source.[checkpoint], source.metadata);
"""

UPSERT_CHECKPOINT_WRITES_SQL = """
    MERGE checkpoint_writes AS target
    USING (SELECT ? AS thread_id, ? AS checkpoint_ns, ? AS checkpoint_id,
                  ? AS task_id, ? AS task_path, ? AS idx, ? AS channel,
                  ? AS [type], ? AS blob) AS source
    ON target.thread_id = source.thread_id
       AND target.checkpoint_ns = source.checkpoint_ns
       AND target.checkpoint_id = source.checkpoint_id
       AND target.task_id = source.task_id
       AND target.idx = source.idx
    WHEN MATCHED THEN
        UPDATE SET channel = source.channel, [type] = source.[type], blob = source.blob
    WHEN NOT MATCHED THEN
        INSERT (thread_id, checkpoint_ns, checkpoint_id, task_id, task_path,
                idx, channel, [type], blob)
        VALUES (source.thread_id, source.checkpoint_ns, source.checkpoint_id,
                source.task_id, source.task_path, source.idx, source.channel,
                source.[type], source.blob);
"""

INSERT_CHECKPOINT_WRITES_SQL = """
    MERGE checkpoint_writes AS target
    USING (SELECT ? AS thread_id, ? AS checkpoint_ns, ? AS checkpoint_id,
                  ? AS task_id, ? AS task_path, ? AS idx, ? AS channel,
                  ? AS [type], ? AS blob) AS source
    ON target.thread_id = source.thread_id
       AND target.checkpoint_ns = source.checkpoint_ns
       AND target.checkpoint_id = source.checkpoint_id
       AND target.task_id = source.task_id
       AND target.idx = source.idx
    WHEN NOT MATCHED THEN
        INSERT (thread_id, checkpoint_ns, checkpoint_id, task_id, task_path,
                idx, channel, [type], blob)
        VALUES (source.thread_id, source.checkpoint_ns, source.checkpoint_id,
                source.task_id, source.task_path, source.idx, source.channel,
                source.[type], source.blob);
"""

# Query for pending sends migration (for checkpoint versions < 4)
SELECT_PENDING_SENDS_SQL = f"""
    SELECT checkpoint_id, [type], blob
    FROM checkpoint_writes
    WHERE thread_id = ? AND checkpoint_id IN ({{placeholders}}) AND channel = '{TASKS}'
    ORDER BY checkpoint_id, task_path, task_id, idx
"""

# Batch query for fetching blobs for multiple checkpoints
# Uses OPENJSON to parse channel_versions from checkpoint JSON and join with blobs
# Note: COLLATE clauses are needed because OPENJSON returns Latin1_General_BIN2 by default
SELECT_BLOBS_SQL = """
    SELECT
        c.thread_id,
        c.checkpoint_ns,
        c.checkpoint_id,
        bl.channel,
        bl.[type],
        bl.blob
    FROM checkpoints c
    CROSS APPLY OPENJSON(c.[checkpoint], '$.channel_versions') cv
    INNER JOIN checkpoint_blobs bl
        ON bl.thread_id = c.thread_id
        AND bl.checkpoint_ns = c.checkpoint_ns
        AND bl.channel = cv.[key] COLLATE SQL_Latin1_General_CP1_CI_AS
        AND bl.version = cv.[value] COLLATE SQL_Latin1_General_CP1_CI_AS
    WHERE c.thread_id = ? AND c.checkpoint_id IN ({placeholders})
"""

# Batch query for fetching writes for multiple checkpoints
SELECT_WRITES_SQL = """
    SELECT
        thread_id,
        checkpoint_ns,
        checkpoint_id,
        task_id,
        channel,
        [type],
        blob
    FROM checkpoint_writes
    WHERE thread_id = ? AND checkpoint_id IN ({placeholders})
    ORDER BY thread_id, checkpoint_ns, checkpoint_id, task_id, idx
"""


class BaseMSSQLSaver(BaseCheckpointSaver[str]):
    """Base class for MSSQL checkpoint savers."""

    MIGRATIONS = MIGRATIONS
    UPSERT_CHECKPOINT_BLOBS_SQL = UPSERT_CHECKPOINT_BLOBS_SQL
    UPSERT_CHECKPOINTS_SQL = UPSERT_CHECKPOINTS_SQL
    UPSERT_CHECKPOINT_WRITES_SQL = UPSERT_CHECKPOINT_WRITES_SQL
    INSERT_CHECKPOINT_WRITES_SQL = INSERT_CHECKPOINT_WRITES_SQL
    SELECT_PENDING_SENDS_SQL = SELECT_PENDING_SENDS_SQL
    SELECT_BLOBS_SQL = SELECT_BLOBS_SQL
    SELECT_WRITES_SQL = SELECT_WRITES_SQL

    def _migrate_pending_sends(
        self,
        pending_sends: list[tuple[str, bytes]],
        checkpoint: dict[str, Any],
        channel_values: dict[str, Any],
    ) -> None:
        """Migrate pending sends from older checkpoint format (v < 4).

        This method converts pending sends stored in checkpoint_writes to
        channel_values in the checkpoint, as required by newer LangGraph versions.
        """
        if not pending_sends:
            return
        # Deserialize and combine all sends
        sends = [
            self.serde.loads_typed(
                (type_.decode() if isinstance(type_, bytes) else type_, blob)
            )
            for type_, blob in pending_sends
        ]
        # Add to channel values
        channel_values[TASKS] = sends
        # Add to channel versions
        checkpoint["channel_versions"][TASKS] = (
            max(checkpoint["channel_versions"].values())
            if checkpoint["channel_versions"]
            else self.get_next_version(None, None)
        )

    def _load_blobs(
        self, blob_values: list[tuple[str, str, bytes | None]]
    ) -> dict[str, Any]:
        """Load blob values from storage format."""
        if not blob_values:
            return {}
        return {
            channel: self.serde.loads_typed((type_, blob))
            for channel, type_, blob in blob_values
            if type_ != "empty" and blob is not None
        }

    def _dump_blobs(
        self,
        thread_id: str,
        checkpoint_ns: str,
        values: dict[str, Any],
        versions: ChannelVersions,
    ) -> list[tuple[str, str, str, str, str, bytes | None]]:
        """Dump blob values for storage."""
        if not versions:
            return []

        result: list[tuple[str, str, str, str, str, bytes | None]] = []
        for k, ver in versions.items():
            if k in values:
                type_, blob = self.serde.dumps_typed(values[k])
            else:
                type_, blob = "empty", None
            result.append((thread_id, checkpoint_ns, k, cast(str, ver), type_, blob))
        return result

    def _load_writes(
        self, writes: list[tuple[str, str, str, bytes]]
    ) -> list[tuple[str, str, Any]]:
        """Load writes from storage format."""
        return (
            [
                (
                    task_id,
                    channel,
                    self.serde.loads_typed((type_, blob)),
                )
                for task_id, channel, type_, blob in writes
            ]
            if writes
            else []
        )

    def _dump_writes(
        self,
        thread_id: str,
        checkpoint_ns: str,
        checkpoint_id: str,
        task_id: str,
        task_path: str,
        writes: Sequence[tuple[str, Any]],
    ) -> list[tuple[str, str, str, str, str, int, str, str, bytes]]:
        """Dump writes for storage."""
        return [
            (
                thread_id,
                checkpoint_ns,
                checkpoint_id,
                task_id,
                task_path,
                WRITES_IDX_MAP.get(channel, idx),
                channel,
                *self.serde.dumps_typed(value),
            )
            for idx, (channel, value) in enumerate(writes)
        ]

    def get_next_version(self, current: str | None, channel: None) -> str:
        """Generate the next version string."""
        if current is None:
            current_v = 0
        elif isinstance(current, int):
            current_v = current
        else:
            current_v = int(current.split(".")[0])
        next_v = current_v + 1
        next_h = random.random()
        return f"{next_v:032}.{next_h:016}"

    def _search_where(
        self,
        config: RunnableConfig | None,
        filter: MetadataInput,
        before: RunnableConfig | None = None,
    ) -> tuple[str, list[Any]]:
        """Build WHERE clause for list queries."""
        wheres = []
        params: list[Any] = []

        if config:
            wheres.append("thread_id = ?")
            params.append(config["configurable"]["thread_id"])

            checkpoint_ns = config["configurable"].get("checkpoint_ns")
            if checkpoint_ns is not None:
                wheres.append("checkpoint_ns = ?")
                params.append(checkpoint_ns)

            if checkpoint_id := get_checkpoint_id(config):
                wheres.append("checkpoint_id = ?")
                params.append(checkpoint_id)

        if filter:
            # Pass filter as JSON parameter, parsed server-side via OPENJSON
            filter_json = json.dumps(
                [
                    {"k": k, "v": v if isinstance(v, str) else json.dumps(v)}
                    for k, v in filter.items()
                ]
            )
            wheres.append(
                f"""(SELECT COUNT(*) FROM OPENJSON(?) WITH (k NVARCHAR(450), v NVARCHAR(MAX)) f
                    WHERE JSON_VALUE(metadata, '$."' + f.k + '"') = f.v) = {len(filter)}"""
            )
            params.append(filter_json)

        if before is not None:
            wheres.append("checkpoint_id < ?")
            params.append(get_checkpoint_id(before))

        return (
            "WHERE " + " AND ".join(wheres) if wheres else "",
            params,
        )
