from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Iterator, Sequence
from contextlib import asynccontextmanager
from typing import Any, cast

import aioodbc
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    WRITES_IDX_MAP,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    get_checkpoint_id,
    get_serializable_checkpoint_metadata,
)
from langgraph.checkpoint.serde.base import SerializerProtocol

from langgraph.checkpoint.mssql.base import BaseMSSQLSaver, MetadataInput


class AsyncMSSQLSaver(BaseMSSQLSaver):
    """Async MSSQL checkpoint saver using aioodbc.

    Example:
        >>> conn_str = (
        ...     "DRIVER={ODBC Driver 18 for SQL Server};"
        ...     "SERVER=localhost;DATABASE=mydb;UID=user;PWD=pass"
        ... )
        >>> async with AsyncMSSQLSaver.from_conn_string(conn_str) as saver:
        ...     await saver.setup()
        ...     # Use with LangGraph
        ...     pass
    """

    pool: aioodbc.Pool
    lock: asyncio.Lock

    def __init__(
        self,
        pool: aioodbc.Pool,
        *,
        serde: SerializerProtocol | None = None,
    ) -> None:
        super().__init__(serde=serde)
        self.pool = pool
        self.lock = asyncio.Lock()
        self.loop = asyncio.get_running_loop()

    @classmethod
    @asynccontextmanager
    async def from_conn_string(
        cls,
        conn_string: str,
        *,
        pool_size: int = 10,
        serde: SerializerProtocol | None = None,
    ) -> AsyncIterator[AsyncMSSQLSaver]:
        """Create an AsyncMSSQLSaver from a connection string.

        Args:
            conn_string: ODBC connection string
            pool_size: Maximum number of connections in the pool
            serde: Optional serializer protocol

        Yields:
            AsyncMSSQLSaver instance
        """
        pool = await aioodbc.create_pool(
            dsn=conn_string,
            minsize=1,
            maxsize=pool_size,
            autocommit=True,
        )
        try:
            yield cls(pool, serde=serde)
        finally:
            pool.close()
            await pool.wait_closed()

    async def setup(self) -> None:
        """Set up the checkpoint database asynchronously.

        This method creates the necessary tables in the database if they don't
        already exist and runs database migrations. It MUST be called directly
        by the user the first time the checkpointer is used.
        """
        async with self.lock:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(self.MIGRATIONS[0])
                    await cursor.execute(
                        "SELECT v FROM checkpoint_migrations ORDER BY v DESC"
                    )
                    row = await cursor.fetchone()
                    version = row[0] if row else -1

                    for v, migration in zip(
                        range(version + 1, len(self.MIGRATIONS)),
                        self.MIGRATIONS[version + 1 :],
                        strict=False,
                    ):
                        await cursor.execute(migration)
                        await cursor.execute(
                            "INSERT INTO checkpoint_migrations (v) VALUES (?)", (v,)
                        )

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: MetadataInput = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """List checkpoints from the database asynchronously.

        This method uses batch fetching to minimize database queries:
        - 1 query for checkpoints
        - 1 query for all blobs across all checkpoints
        - 1 query for all writes across all checkpoints

        Args:
            config: Base configuration for filtering checkpoints.
            filter: Additional filtering criteria for metadata.
            before: List checkpoints before this configuration.
            limit: Maximum number of checkpoints to return.

        Yields:
            Async iterator of checkpoint tuples.
        """
        where, params = self._search_where(config, filter, before)
        query = f"""
            SELECT {"TOP " + str(limit) if limit else ""}
                thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id,
                [checkpoint], metadata
            FROM checkpoints
            {where}
            ORDER BY checkpoint_id DESC
        """

        async with self.lock:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, params)
                    rows = await cursor.fetchall()

                    if not rows:
                        return

                    # Get unique thread_id and checkpoint_ids for batch fetching
                    thread_id = rows[0][0]
                    checkpoint_ids = [row[2] for row in rows]

                    # Batch fetch all blobs for all checkpoints in one query
                    blobs_map = await self._fetch_blobs_batch(
                        cursor, thread_id, checkpoint_ids
                    )

                    # Batch fetch all writes for all checkpoints in one query
                    writes_map = await self._fetch_writes_batch(
                        cursor, thread_id, checkpoint_ids
                    )

                    # Check for rows needing pending sends migration (checkpoint v < 4)
                    to_migrate = []
                    for row in rows:
                        checkpoint_dict = json.loads(row[4])  # checkpoint JSON
                        if (
                            checkpoint_dict.get("v", 0) < 4 and row[3]
                        ):  # parent_checkpoint_id
                            to_migrate.append(row[3])  # parent_checkpoint_id

                    # Fetch pending sends for migration in one batch
                    pending_sends_map: dict[str, list[tuple[str, bytes]]] = {}
                    if to_migrate:
                        pending_sends_map = (
                            await self._fetch_pending_sends_for_migration(
                                cursor, thread_id, to_migrate
                            )
                        )

                    for row in rows:
                        checkpoint_id = row[2]
                        parent_checkpoint_id = row[3]
                        pending_sends = pending_sends_map.get(parent_checkpoint_id)
                        yield await self._load_checkpoint_data_with_batch(
                            row,
                            blobs_map.get(checkpoint_id, []),
                            writes_map.get(checkpoint_id, []),
                            pending_sends,
                        )

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Get a checkpoint tuple from the database asynchronously.

        Args:
            config: Configuration specifying which checkpoint to retrieve.

        Returns:
            The checkpoint tuple, or None if not found.
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = get_checkpoint_id(config)
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

        async with self.lock:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    if checkpoint_id:
                        await cursor.execute(
                            """SELECT thread_id, checkpoint_ns, checkpoint_id,
                                      parent_checkpoint_id, [checkpoint], metadata
                               FROM checkpoints
                               WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?""",
                            (thread_id, checkpoint_ns, checkpoint_id),
                        )
                    else:
                        await cursor.execute(
                            """SELECT TOP 1 thread_id, checkpoint_ns, checkpoint_id,
                                          parent_checkpoint_id, [checkpoint], metadata
                               FROM checkpoints
                               WHERE thread_id = ? AND checkpoint_ns = ?
                               ORDER BY checkpoint_id DESC""",
                            (thread_id, checkpoint_ns),
                        )

                    row = await cursor.fetchone()
                    if row is None:
                        return None

                    # Check for pending sends migration (checkpoint v < 4)
                    pending_sends = None
                    checkpoint_dict = json.loads(row[4])
                    parent_checkpoint_id = row[3]
                    if checkpoint_dict.get("v", 0) < 4 and parent_checkpoint_id:
                        pending_sends_map = (
                            await self._fetch_pending_sends_for_migration(
                                cursor, thread_id, [parent_checkpoint_id]
                            )
                        )
                        pending_sends = pending_sends_map.get(parent_checkpoint_id)

                    return await self._load_checkpoint_data(row, cursor, pending_sends)

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Save a checkpoint to the database asynchronously.

        Args:
            config: Configuration for the checkpoint.
            checkpoint: The checkpoint to save.
            metadata: Additional metadata for the checkpoint.
            new_versions: New channel versions as of this write.

        Returns:
            Updated configuration after storing the checkpoint.
        """
        configurable = config["configurable"].copy()
        thread_id = configurable.pop("thread_id")
        checkpoint_ns = configurable.pop("checkpoint_ns", "")
        parent_checkpoint_id = configurable.pop("checkpoint_id", None)

        # Make a copy to avoid mutating the original
        copy: dict[str, Any] = dict(checkpoint)
        copy["channel_values"] = dict(copy.get("channel_values") or {})

        # Separate primitive values (inline) from blob values
        blob_values: dict[str, Any] = {}
        for k, v in (checkpoint.get("channel_values") or {}).items():
            if v is None or isinstance(v, (str, int, float, bool)):
                pass
            else:
                blob_values[k] = copy["channel_values"].pop(k)

        next_config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

        async with self.lock:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Save blobs
                    blob_versions = {
                        k: v for k, v in new_versions.items() if k in blob_values
                    }
                    if blob_versions:
                        blob_params_list = await asyncio.to_thread(
                            self._dump_blobs,
                            thread_id,
                            checkpoint_ns,
                            blob_values,
                            blob_versions,
                        )
                        for blob_params in blob_params_list:
                            await cursor.execute(
                                self.UPSERT_CHECKPOINT_BLOBS_SQL, blob_params
                            )

                    # Save checkpoint
                    await cursor.execute(
                        self.UPSERT_CHECKPOINTS_SQL,
                        (
                            thread_id,
                            checkpoint_ns,
                            checkpoint["id"],
                            parent_checkpoint_id,
                            json.dumps(copy),
                            json.dumps(
                                get_serializable_checkpoint_metadata(config, metadata)
                            ),
                        ),
                    )

        return next_config

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Store intermediate writes linked to a checkpoint asynchronously.

        Args:
            config: Configuration of the related checkpoint.
            writes: List of writes to store.
            task_id: Identifier for the task creating the writes.
            task_path: Path of the task creating the writes.
        """
        query = (
            self.UPSERT_CHECKPOINT_WRITES_SQL
            if all(w[0] in WRITES_IDX_MAP for w in writes)
            else self.INSERT_CHECKPOINT_WRITES_SQL
        )

        params_list = await asyncio.to_thread(
            self._dump_writes,
            config["configurable"]["thread_id"],
            config["configurable"].get("checkpoint_ns", ""),
            config["configurable"]["checkpoint_id"],
            task_id,
            task_path,
            writes,
        )

        async with self.lock:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    for params in params_list:
                        await cursor.execute(query, params)

    async def adelete_thread(self, thread_id: str) -> None:
        """Delete all checkpoints and writes for a thread asynchronously.

        Args:
            thread_id: The thread ID to delete.
        """
        async with self.lock:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM checkpoint_writes WHERE thread_id = ?",
                        (thread_id,),
                    )
                    await cursor.execute(
                        "DELETE FROM checkpoint_blobs WHERE thread_id = ?",
                        (thread_id,),
                    )
                    await cursor.execute(
                        "DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,)
                    )

    async def _load_checkpoint_data(
        self,
        row: tuple[Any, ...],
        cursor: Any,
        pending_sends: list[tuple[str, bytes]] | None = None,
    ) -> CheckpointTuple:
        """Load checkpoint data from a database row asynchronously."""
        (
            thread_id,
            checkpoint_ns,
            checkpoint_id,
            parent_checkpoint_id,
            checkpoint_json,
            metadata_json,
        ) = row

        checkpoint_dict = json.loads(checkpoint_json)

        # Load channel values (blobs)
        channel_values = await self._fetch_blobs(
            cursor,
            thread_id,
            checkpoint_ns,
            checkpoint_dict.get("channel_versions") or {},
        )

        # Apply pending sends migration if provided (for checkpoint v < 4)
        if pending_sends:
            self._migrate_pending_sends(pending_sends, checkpoint_dict, channel_values)

        # Load pending writes
        await cursor.execute(
            """SELECT task_id, channel, [type], blob FROM checkpoint_writes
               WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?
               ORDER BY task_id, idx""",
            (thread_id, checkpoint_ns, checkpoint_id),
        )
        pending_writes = await asyncio.to_thread(
            self._load_writes, list(await cursor.fetchall())
        )

        # Merge blob values with inline values
        checkpoint_dict["channel_values"] = {
            **(checkpoint_dict.get("channel_values") or {}),
            **channel_values,
        }

        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": checkpoint_id,
                }
            },
            checkpoint=cast(Checkpoint, checkpoint_dict),
            metadata=json.loads(metadata_json) if metadata_json else {},
            parent_config=(
                {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": parent_checkpoint_id,
                    }
                }
                if parent_checkpoint_id
                else None
            ),
            pending_writes=pending_writes,
        )

    async def _fetch_pending_sends_for_migration(
        self,
        cursor: Any,
        thread_id: str,
        parent_checkpoint_ids: list[str],
    ) -> dict[str, list[tuple[str, bytes]]]:
        """Fetch pending sends for checkpoint migration asynchronously."""
        if not parent_checkpoint_ids:
            return {}

        placeholders = ",".join(["?"] * len(parent_checkpoint_ids))
        query = self.SELECT_PENDING_SENDS_SQL.format(placeholders=placeholders)
        await cursor.execute(query, [thread_id] + parent_checkpoint_ids)

        # Group by checkpoint_id
        result: dict[str, list[tuple[str, bytes]]] = {}
        for row in await cursor.fetchall():
            checkpoint_id, type_, blob = row
            if checkpoint_id not in result:
                result[checkpoint_id] = []
            result[checkpoint_id].append((type_, blob))
        return result

    async def _fetch_blobs(
        self,
        cursor: Any,
        thread_id: str,
        checkpoint_ns: str,
        channel_versions: dict[str, str],
    ) -> dict[str, Any]:
        """Fetch blob values for a checkpoint in a single query asynchronously."""
        if not channel_versions:
            return {}

        # Build a single query with OR conditions for all channel/version pairs
        # This is more efficient than N separate queries
        conditions = []
        params: list[Any] = [thread_id, checkpoint_ns]
        for channel, version in channel_versions.items():
            conditions.append("(channel = ? AND version = ?)")
            params.extend([channel, version])

        query = f"""
            SELECT channel, [type], blob FROM checkpoint_blobs
            WHERE thread_id = ? AND checkpoint_ns = ? AND ({" OR ".join(conditions)})
        """
        await cursor.execute(query, params)
        blob_values = [(row[0], row[1], row[2]) for row in await cursor.fetchall()]

        return await asyncio.to_thread(self._load_blobs, blob_values)

    async def _fetch_blobs_batch(
        self,
        cursor: Any,
        thread_id: str,
        checkpoint_ids: list[str],
    ) -> dict[str, list[tuple[str, str, bytes | None]]]:
        """Batch fetch blobs for multiple checkpoints in a single query.

        Uses OPENJSON to parse channel_versions from checkpoint JSON and join with blobs.

        Returns:
            Dict mapping checkpoint_id -> list of (channel, type, blob) tuples
        """
        if not checkpoint_ids:
            return {}

        placeholders = ",".join(["?"] * len(checkpoint_ids))
        query = self.SELECT_BLOBS_SQL.format(placeholders=placeholders)
        await cursor.execute(query, [thread_id] + checkpoint_ids)

        # Group by checkpoint_id
        result: dict[str, list[tuple[str, str, bytes | None]]] = {}
        for row in await cursor.fetchall():
            # row: thread_id, checkpoint_ns, checkpoint_id, channel, type, blob
            checkpoint_id = row[2]
            if checkpoint_id not in result:
                result[checkpoint_id] = []
            result[checkpoint_id].append((row[3], row[4], row[5]))
        return result

    async def _fetch_writes_batch(
        self,
        cursor: Any,
        thread_id: str,
        checkpoint_ids: list[str],
    ) -> dict[str, list[tuple[str, str, str, bytes]]]:
        """Batch fetch writes for multiple checkpoints in a single query.

        Returns:
            Dict mapping checkpoint_id -> list of (task_id, channel, type, blob) tuples
        """
        if not checkpoint_ids:
            return {}

        placeholders = ",".join(["?"] * len(checkpoint_ids))
        query = self.SELECT_WRITES_SQL.format(placeholders=placeholders)
        await cursor.execute(query, [thread_id] + checkpoint_ids)

        # Group by checkpoint_id
        result: dict[str, list[tuple[str, str, str, bytes]]] = {}
        for row in await cursor.fetchall():
            # row: thread_id, checkpoint_ns, checkpoint_id, task_id, channel, type, blob
            checkpoint_id = row[2]
            if checkpoint_id not in result:
                result[checkpoint_id] = []
            result[checkpoint_id].append((row[3], row[4], row[5], row[6]))
        return result

    async def _load_checkpoint_data_with_batch(
        self,
        row: tuple[Any, ...],
        blob_values: list[tuple[str, str, bytes | None]],
        write_values: list[tuple[str, str, str, bytes]],
        pending_sends: list[tuple[str, bytes]] | None = None,
    ) -> CheckpointTuple:
        """Load checkpoint data using pre-fetched blobs and writes.

        This is used by alist() for batch loading to avoid N+1 queries.
        """
        (
            thread_id,
            checkpoint_ns,
            checkpoint_id,
            parent_checkpoint_id,
            checkpoint_json,
            metadata_json,
        ) = row

        checkpoint_dict = json.loads(checkpoint_json)

        # Load channel values from pre-fetched blobs
        channel_values = await asyncio.to_thread(self._load_blobs, blob_values)

        # Apply pending sends migration if provided (for checkpoint v < 4)
        if pending_sends:
            self._migrate_pending_sends(pending_sends, checkpoint_dict, channel_values)

        # Load pending writes from pre-fetched writes
        pending_writes = await asyncio.to_thread(self._load_writes, write_values)

        # Merge blob values with inline values
        checkpoint_dict["channel_values"] = {
            **(checkpoint_dict.get("channel_values") or {}),
            **channel_values,
        }

        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": checkpoint_id,
                }
            },
            checkpoint=cast(Checkpoint, checkpoint_dict),
            metadata=json.loads(metadata_json) if metadata_json else {},
            parent_config=(
                {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": parent_checkpoint_id,
                    }
                }
                if parent_checkpoint_id
                else None
            ),
            pending_writes=pending_writes,
        )

    # Sync methods that delegate to async methods (for backwards compatibility)

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: MetadataInput = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints from the database (sync wrapper).

        Args:
            config: Base configuration for filtering checkpoints.
            filter: Additional filtering criteria for metadata.
            before: List checkpoints before this configuration.
            limit: Maximum number of checkpoints to return.

        Yields:
            Iterator of checkpoint tuples.
        """
        try:
            if asyncio.get_running_loop() is self.loop:
                raise asyncio.InvalidStateError(
                    "Synchronous calls to AsyncMSSQLSaver are only allowed from a "
                    "different thread. From the main thread, use the async interface."
                )
        except RuntimeError:
            pass

        aiter_ = self.alist(config, filter=filter, before=before, limit=limit)
        while True:
            try:
                yield asyncio.run_coroutine_threadsafe(
                    anext(aiter_),  # type: ignore[arg-type]
                    self.loop,
                ).result()
            except StopAsyncIteration:
                break

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Get a checkpoint tuple from the database (sync wrapper).

        Args:
            config: Configuration specifying which checkpoint to retrieve.

        Returns:
            The checkpoint tuple, or None if not found.
        """
        try:
            if asyncio.get_running_loop() is self.loop:
                raise asyncio.InvalidStateError(
                    "Synchronous calls to AsyncMSSQLSaver are only allowed from a "
                    "different thread. From the main thread, use the async interface."
                )
        except RuntimeError:
            pass

        return asyncio.run_coroutine_threadsafe(
            self.aget_tuple(config), self.loop
        ).result()

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Save a checkpoint to the database (sync wrapper).

        Args:
            config: Configuration for the checkpoint.
            checkpoint: The checkpoint to save.
            metadata: Additional metadata for the checkpoint.
            new_versions: New channel versions as of this write.

        Returns:
            Updated configuration after storing the checkpoint.
        """
        return asyncio.run_coroutine_threadsafe(
            self.aput(config, checkpoint, metadata, new_versions), self.loop
        ).result()

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Store intermediate writes linked to a checkpoint (sync wrapper).

        Args:
            config: Configuration of the related checkpoint.
            writes: List of writes to store.
            task_id: Identifier for the task creating the writes.
            task_path: Path of the task creating the writes.
        """
        return asyncio.run_coroutine_threadsafe(
            self.aput_writes(config, writes, task_id, task_path), self.loop
        ).result()

    def delete_thread(self, thread_id: str) -> None:
        """Delete all checkpoints and writes for a thread (sync wrapper).

        Args:
            thread_id: The thread ID to delete.
        """
        try:
            if asyncio.get_running_loop() is self.loop:
                raise asyncio.InvalidStateError(
                    "Synchronous calls to AsyncMSSQLSaver are only allowed from a "
                    "different thread. From the main thread, use the async interface."
                )
        except RuntimeError:
            pass

        return asyncio.run_coroutine_threadsafe(
            self.adelete_thread(thread_id), self.loop
        ).result()


__all__ = ["AsyncMSSQLSaver"]
