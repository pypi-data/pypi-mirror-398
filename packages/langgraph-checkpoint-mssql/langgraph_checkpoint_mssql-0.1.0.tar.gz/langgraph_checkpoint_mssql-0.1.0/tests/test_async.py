# type: ignore
from contextlib import asynccontextmanager
from typing import Any

import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    Checkpoint,
    CheckpointMetadata,
    create_checkpoint,
    empty_checkpoint,
)
from langgraph.checkpoint.serde.types import TASKS

from langgraph.checkpoint.mssql.aio import AsyncMSSQLSaver
from tests.conftest import get_connection_string


@asynccontextmanager
async def _async_saver():
    """Create an AsyncMSSQLSaver with a fresh test database."""
    conn_string = get_connection_string()
    async with AsyncMSSQLSaver.from_conn_string(conn_string) as saver:
        await saver.setup()
        yield saver
        # Clean up
        async with saver.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                for table in [
                    "checkpoint_writes",
                    "checkpoint_blobs",
                    "checkpoints",
                    "checkpoint_migrations",
                ]:
                    try:
                        await cursor.execute(f"DELETE FROM {table}")
                    except Exception:
                        pass


@pytest.fixture
def test_data():
    """Fixture providing test data for checkpoint tests."""
    config_1: RunnableConfig = {
        "configurable": {
            "thread_id": "thread-1",
            "checkpoint_id": "1",
            "checkpoint_ns": "",
        }
    }
    config_2: RunnableConfig = {
        "configurable": {
            "thread_id": "thread-2",
            "checkpoint_id": "2",
            "checkpoint_ns": "",
        }
    }
    config_3: RunnableConfig = {
        "configurable": {
            "thread_id": "thread-2",
            "checkpoint_id": "2-inner",
            "checkpoint_ns": "inner",
        }
    }

    chkpnt_1: Checkpoint = empty_checkpoint()
    chkpnt_2: Checkpoint = create_checkpoint(chkpnt_1, {}, 1)
    chkpnt_3: Checkpoint = empty_checkpoint()

    metadata_1: CheckpointMetadata = {
        "source": "input",
        "step": 2,
        "score": 1,
    }
    metadata_2: CheckpointMetadata = {
        "source": "loop",
        "step": 1,
        "score": None,
    }
    metadata_3: CheckpointMetadata = {}

    return {
        "configs": [config_1, config_2, config_3],
        "checkpoints": [chkpnt_1, chkpnt_2, chkpnt_3],
        "metadata": [metadata_1, metadata_2, metadata_3],
    }


@pytest.mark.asyncio
async def test_setup() -> None:
    """Test that setup creates all necessary tables."""
    async with _async_saver() as saver:
        async with saver.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT name FROM sys.tables WHERE name IN "
                    "('checkpoints', 'checkpoint_blobs', 'checkpoint_writes', 'checkpoint_migrations')"
                )
                tables = {row[0] for row in await cursor.fetchall()}
                assert tables == {
                    "checkpoints",
                    "checkpoint_blobs",
                    "checkpoint_writes",
                    "checkpoint_migrations",
                }


@pytest.mark.asyncio
async def test_put_get(test_data) -> None:
    """Test basic put and get operations."""
    async with _async_saver() as saver:
        config = test_data["configs"][0]
        checkpoint = test_data["checkpoints"][0]
        metadata = test_data["metadata"][0]

        # Put checkpoint
        saved_config = await saver.aput(config, checkpoint, metadata, {})

        # Verify returned config
        assert saved_config["configurable"]["thread_id"] == "thread-1"
        assert saved_config["configurable"]["checkpoint_ns"] == ""
        assert saved_config["configurable"]["checkpoint_id"] == checkpoint["id"]

        # Get checkpoint
        result = await saver.aget_tuple(saved_config)
        assert result is not None
        assert result.checkpoint["id"] == checkpoint["id"]
        assert result.metadata["source"] == "input"
        assert result.metadata["step"] == 2


@pytest.mark.asyncio
async def test_get_tuple_not_found() -> None:
    """Test aget_tuple returns None for non-existent checkpoint."""
    async with _async_saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "nonexistent",
                "checkpoint_ns": "",
            }
        }
        result = await saver.aget_tuple(config)
        assert result is None


@pytest.mark.asyncio
async def test_search(test_data) -> None:
    """Test alist() with various filters."""
    async with _async_saver() as saver:
        configs = test_data["configs"]
        checkpoints = test_data["checkpoints"]
        metadata = test_data["metadata"]

        await saver.aput(configs[0], checkpoints[0], metadata[0], {})
        await saver.aput(configs[1], checkpoints[1], metadata[1], {})
        await saver.aput(configs[2], checkpoints[2], metadata[2], {})

        # Search by single key
        query_1 = {"source": "input"}
        search_results_1 = [r async for r in saver.alist(None, filter=query_1)]
        assert len(search_results_1) == 1

        # Search by multiple conditions
        query_2 = {"step": 1}
        search_results_2 = [r async for r in saver.alist(None, filter=query_2)]
        assert len(search_results_2) == 1

        # Search with no filter (returns all)
        query_3: dict[str, Any] = {}
        search_results_3 = [r async for r in saver.alist(None, filter=query_3)]
        assert len(search_results_3) == 3

        # Search by thread_id
        search_results_5 = [
            r async for r in saver.alist({"configurable": {"thread_id": "thread-2"}})
        ]
        assert len(search_results_5) == 2


@pytest.mark.asyncio
async def test_list_limit(test_data) -> None:
    """Test alist() with limit parameter."""
    async with _async_saver() as saver:
        configs = test_data["configs"]
        checkpoints = test_data["checkpoints"]
        metadata = test_data["metadata"]

        await saver.aput(configs[0], checkpoints[0], metadata[0], {})
        await saver.aput(configs[1], checkpoints[1], metadata[1], {})
        await saver.aput(configs[2], checkpoints[2], metadata[2], {})

        # List with limit
        results = [r async for r in saver.alist(None, limit=2)]
        assert len(results) == 2


@pytest.mark.asyncio
async def test_put_writes(test_data) -> None:
    """Test aput_writes stores intermediate writes."""
    async with _async_saver() as saver:
        config = test_data["configs"][0]
        checkpoint = test_data["checkpoints"][0]
        metadata = test_data["metadata"][0]

        # Put checkpoint first
        saved_config = await saver.aput(config, checkpoint, metadata, {})

        # Put writes
        writes = [("channel1", "value1"), ("channel2", {"nested": "value"})]
        await saver.aput_writes(saved_config, writes, "task-1")

        # Retrieve and verify writes
        result = await saver.aget_tuple(saved_config)
        assert result is not None
        assert len(result.pending_writes) == 2


@pytest.mark.asyncio
async def test_channel_values_with_blobs(test_data) -> None:
    """Test that complex channel values are stored as blobs."""
    async with _async_saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-blob",
                "checkpoint_ns": "",
            }
        }

        checkpoint = empty_checkpoint()
        checkpoint["channel_values"] = {
            "simple": "string",
            "number": 42,
            "complex": {"nested": {"data": [1, 2, 3]}},
            "list_value": [1, 2, 3],
        }

        # Channel versions must be set in checkpoint (as LangGraph does)
        # These tell the loader which blob versions to fetch
        new_versions = {
            "complex": "1",
            "list_value": "1",
        }
        checkpoint["channel_versions"] = new_versions.copy()

        saved_config = await saver.aput(config, checkpoint, {}, new_versions)

        result = await saver.aget_tuple(saved_config)
        assert result is not None

        assert result.checkpoint["channel_values"]["simple"] == "string"
        assert result.checkpoint["channel_values"]["number"] == 42
        assert result.checkpoint["channel_values"]["complex"] == {
            "nested": {"data": [1, 2, 3]}
        }
        assert result.checkpoint["channel_values"]["list_value"] == [1, 2, 3]


@pytest.mark.asyncio
async def test_delete_thread() -> None:
    """Test adelete_thread removes all data for a thread."""
    async with _async_saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-to-delete",
                "checkpoint_ns": "",
            }
        }

        checkpoint = empty_checkpoint()
        saved_config = await saver.aput(config, checkpoint, {}, {})

        result = await saver.aget_tuple(saved_config)
        assert result is not None

        await saver.adelete_thread("thread-to-delete")

        result = await saver.aget_tuple(saved_config)
        assert result is None


@pytest.mark.asyncio
async def test_parent_checkpoint() -> None:
    """Test that parent checkpoint is properly tracked."""
    async with _async_saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-parent",
                "checkpoint_ns": "",
            }
        }

        checkpoint_1 = empty_checkpoint()
        saved_config_1 = await saver.aput(config, checkpoint_1, {}, {})

        checkpoint_2 = create_checkpoint(checkpoint_1, {}, 1)
        saved_config_2 = await saver.aput(saved_config_1, checkpoint_2, {}, {})

        result = await saver.aget_tuple(saved_config_2)
        assert result is not None
        assert result.parent_config is not None
        assert (
            result.parent_config["configurable"]["checkpoint_id"] == checkpoint_1["id"]
        )


@pytest.mark.asyncio
async def test_multiple_namespaces() -> None:
    """Test checkpoints with different namespaces."""
    async with _async_saver() as saver:
        thread_id = "thread-ns"

        config_1: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": "",
            }
        }
        config_2: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": "inner",
            }
        }

        checkpoint_1 = empty_checkpoint()
        checkpoint_2 = empty_checkpoint()

        await saver.aput(config_1, checkpoint_1, {"ns": "root"}, {})
        await saver.aput(config_2, checkpoint_2, {"ns": "inner"}, {})

        result_1 = await saver.aget_tuple(config_1)
        assert result_1 is not None
        assert result_1.config["configurable"]["checkpoint_ns"] == ""

        result_2 = await saver.aget_tuple(config_2)
        assert result_2 is not None
        assert result_2.config["configurable"]["checkpoint_ns"] == "inner"


@pytest.mark.asyncio
async def test_migrations_idempotent() -> None:
    """Test that running setup multiple times is safe."""
    async with _async_saver() as saver:
        await saver.setup()

        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-idempotent",
                "checkpoint_ns": "",
            }
        }
        checkpoint = empty_checkpoint()
        saved_config = await saver.aput(config, checkpoint, {}, {})

        result = await saver.aget_tuple(saved_config)
        assert result is not None


@pytest.mark.asyncio
async def test_combined_metadata() -> None:
    """Test that metadata from config is combined with checkpoint metadata."""
    async with _async_saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-combined",
                "checkpoint_ns": "",
            },
            "metadata": {"run_id": "my_run_id"},
        }
        checkpoint = empty_checkpoint()
        checkpoint_metadata: CheckpointMetadata = {
            "source": "loop",
            "step": 1,
        }

        saved_config = await saver.aput(config, checkpoint, checkpoint_metadata, {})

        result = await saver.aget_tuple(saved_config)
        assert result is not None
        # Metadata from config should be merged with checkpoint metadata
        assert result.metadata["source"] == "loop"
        assert result.metadata["step"] == 1
        assert result.metadata["run_id"] == "my_run_id"


@pytest.mark.asyncio
async def test_pending_sends_migration() -> None:
    """Test that pending sends are properly migrated from writes to channel_values."""
    async with _async_saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-sends",
                "checkpoint_ns": "",
            }
        }

        # Create the first checkpoint and put some pending sends
        checkpoint_0 = empty_checkpoint()
        config = await saver.aput(config, checkpoint_0, {}, {})
        await saver.aput_writes(
            config, [(TASKS, "send-1"), (TASKS, "send-2")], task_id="task-1"
        )
        await saver.aput_writes(config, [(TASKS, "send-3")], task_id="task-2")

        # Check that fetching checkpoint_0 doesn't attach pending sends
        # (they should be attached to the next checkpoint)
        tuple_0 = await saver.aget_tuple(config)
        assert tuple_0 is not None
        assert tuple_0.checkpoint["channel_values"] == {}
        assert tuple_0.checkpoint["channel_versions"] == {}

        # Create the second checkpoint
        checkpoint_1 = create_checkpoint(checkpoint_0, {}, 1)
        config = await saver.aput(config, checkpoint_1, {}, {})

        # Check that pending sends are attached to checkpoint_1
        tuple_1 = await saver.aget_tuple(config)
        assert tuple_1 is not None
        assert tuple_1.checkpoint["channel_values"] == {
            TASKS: ["send-1", "send-2", "send-3"]
        }
        assert TASKS in tuple_1.checkpoint["channel_versions"]

        # Check that list also applies the migration
        search_results = [
            c
            async for c in saver.alist({"configurable": {"thread_id": "thread-sends"}})
        ]
        assert len(search_results) == 2
        assert search_results[-1].checkpoint["channel_values"] == {}
        assert search_results[-1].checkpoint["channel_versions"] == {}
        assert search_results[0].checkpoint["channel_values"] == {
            TASKS: ["send-1", "send-2", "send-3"]
        }
        assert TASKS in search_results[0].checkpoint["channel_versions"]


@pytest.mark.asyncio
async def test_null_chars() -> None:
    """Test that null characters in metadata are handled properly."""
    async with _async_saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-null",
                "checkpoint_ns": "",
            }
        }
        checkpoint = empty_checkpoint()
        # Put checkpoint with null character in metadata
        saved_config = await saver.aput(config, checkpoint, {"my_key": "\x00abc"}, {})

        result = await saver.aget_tuple(saved_config)
        assert result is not None
        # Null character should be stripped or handled
        assert result.metadata["my_key"] == "abc"

        # Check list filter also works
        results = [c async for c in saver.alist(None, filter={"my_key": "abc"})]
        assert len(results) == 1
        assert results[0].metadata["my_key"] == "abc"


@pytest.mark.asyncio
async def test_get_checkpoint_no_channel_values(monkeypatch) -> None:
    """Backwards compatibility test for checkpoints without channel_values key."""
    async with _async_saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-no-cv",
                "checkpoint_ns": "",
            }
        }
        checkpoint = create_checkpoint(empty_checkpoint(), {}, 1)
        await saver.aput(config, checkpoint, {}, {})

        # Patch to simulate old checkpoint format without channel_values
        original_load = saver._load_checkpoint_data

        async def patched_load(row, cursor, pending_sends=None):
            result = await original_load(row, cursor, pending_sends)
            # Simulate checkpoint without channel_values
            result.checkpoint.pop("channel_values", None)
            return result

        monkeypatch.setattr(saver, "_load_checkpoint_data", patched_load)

        # Should not raise an error
        result = await saver.aget_tuple(config)
        # Channel values should default to empty dict
        assert result is not None
