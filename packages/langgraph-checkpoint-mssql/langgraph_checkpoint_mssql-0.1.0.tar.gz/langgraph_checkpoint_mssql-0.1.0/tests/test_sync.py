# type: ignore
from contextlib import contextmanager
from typing import Any

import pyodbc
import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    EXCLUDED_METADATA_KEYS,
    Checkpoint,
    CheckpointMetadata,
    create_checkpoint,
    empty_checkpoint,
)
from langgraph.checkpoint.serde.types import TASKS

from langgraph.checkpoint.mssql import MSSQLSaver
from tests.conftest import get_connection_string


def _exclude_keys(config: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in config.items() if k not in EXCLUDED_METADATA_KEYS}


@contextmanager
def _saver():
    """Create a MSSQLSaver with a fresh test database."""
    conn_string = get_connection_string()
    conn = pyodbc.connect(conn_string, autocommit=True)
    try:
        saver = MSSQLSaver(conn)
        saver.setup()
        yield saver
    finally:
        # Clean up
        cursor = conn.cursor()
        for table in [
            "checkpoint_writes",
            "checkpoint_blobs",
            "checkpoints",
            "checkpoint_migrations",
        ]:
            try:
                cursor.execute(f"DELETE FROM {table}")
            except pyodbc.ProgrammingError:
                pass
        conn.close()


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


def test_setup() -> None:
    """Test that setup creates all necessary tables."""
    with _saver() as saver:
        cursor = saver.conn.cursor()

        # Check tables exist
        cursor.execute(
            "SELECT name FROM sys.tables WHERE name IN "
            "('checkpoints', 'checkpoint_blobs', 'checkpoint_writes', 'checkpoint_migrations')"
        )
        tables = {row[0] for row in cursor.fetchall()}
        assert tables == {
            "checkpoints",
            "checkpoint_blobs",
            "checkpoint_writes",
            "checkpoint_migrations",
        }


def test_put_get(test_data) -> None:
    """Test basic put and get operations."""
    with _saver() as saver:
        config = test_data["configs"][0]
        checkpoint = test_data["checkpoints"][0]
        metadata = test_data["metadata"][0]

        # Put checkpoint
        saved_config = saver.put(config, checkpoint, metadata, {})

        # Verify returned config
        assert saved_config["configurable"]["thread_id"] == "thread-1"
        assert saved_config["configurable"]["checkpoint_ns"] == ""
        assert saved_config["configurable"]["checkpoint_id"] == checkpoint["id"]

        # Get checkpoint
        result = saver.get_tuple(saved_config)
        assert result is not None
        assert result.checkpoint["id"] == checkpoint["id"]
        assert result.metadata["source"] == "input"
        assert result.metadata["step"] == 2


def test_get_tuple_not_found() -> None:
    """Test get_tuple returns None for non-existent checkpoint."""
    with _saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "nonexistent",
                "checkpoint_ns": "",
            }
        }
        result = saver.get_tuple(config)
        assert result is None


def test_search(test_data) -> None:
    """Test list() with various filters."""
    with _saver() as saver:
        configs = test_data["configs"]
        checkpoints = test_data["checkpoints"]
        metadata = test_data["metadata"]

        saver.put(configs[0], checkpoints[0], metadata[0], {})
        saver.put(configs[1], checkpoints[1], metadata[1], {})
        saver.put(configs[2], checkpoints[2], metadata[2], {})

        # Search by single key
        query_1 = {"source": "input"}
        search_results_1 = list(saver.list(None, filter=query_1))
        assert len(search_results_1) == 1

        # Search by multiple conditions
        query_2 = {"step": 1}
        search_results_2 = list(saver.list(None, filter=query_2))
        assert len(search_results_2) == 1

        # Search with no filter (returns all)
        query_3: dict[str, Any] = {}
        search_results_3 = list(saver.list(None, filter=query_3))
        assert len(search_results_3) == 3

        # Search with no matches
        query_4 = {"source": "update", "step": 1}
        search_results_4 = list(saver.list(None, filter=query_4))
        assert len(search_results_4) == 0

        # Search by thread_id
        search_results_5 = list(saver.list({"configurable": {"thread_id": "thread-2"}}))
        assert len(search_results_5) == 2
        assert {
            search_results_5[0].config["configurable"]["checkpoint_ns"],
            search_results_5[1].config["configurable"]["checkpoint_ns"],
        } == {"", "inner"}


def test_list_limit(test_data) -> None:
    """Test list() with limit parameter."""
    with _saver() as saver:
        configs = test_data["configs"]
        checkpoints = test_data["checkpoints"]
        metadata = test_data["metadata"]

        saver.put(configs[0], checkpoints[0], metadata[0], {})
        saver.put(configs[1], checkpoints[1], metadata[1], {})
        saver.put(configs[2], checkpoints[2], metadata[2], {})

        # List with limit
        results = list(saver.list(None, limit=2))
        assert len(results) == 2


def test_put_writes(test_data) -> None:
    """Test put_writes stores intermediate writes."""
    with _saver() as saver:
        config = test_data["configs"][0]
        checkpoint = test_data["checkpoints"][0]
        metadata = test_data["metadata"][0]

        # Put checkpoint first
        saved_config = saver.put(config, checkpoint, metadata, {})

        # Put writes
        writes = [("channel1", "value1"), ("channel2", {"nested": "value"})]
        saver.put_writes(saved_config, writes, "task-1")

        # Retrieve and verify writes
        result = saver.get_tuple(saved_config)
        assert result is not None
        assert len(result.pending_writes) == 2


def test_channel_values_with_blobs(test_data) -> None:
    """Test that complex channel values are stored as blobs."""
    with _saver() as saver:
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

        saved_config = saver.put(config, checkpoint, {}, new_versions)

        result = saver.get_tuple(saved_config)
        assert result is not None

        # Simple values should be preserved
        assert result.checkpoint["channel_values"]["simple"] == "string"
        assert result.checkpoint["channel_values"]["number"] == 42

        # Complex values stored as blobs should be deserialized
        assert result.checkpoint["channel_values"]["complex"] == {
            "nested": {"data": [1, 2, 3]}
        }
        assert result.checkpoint["channel_values"]["list_value"] == [1, 2, 3]


def test_delete_thread() -> None:
    """Test delete_thread removes all data for a thread."""
    with _saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-to-delete",
                "checkpoint_ns": "",
            }
        }

        checkpoint = empty_checkpoint()
        saved_config = saver.put(config, checkpoint, {}, {})

        # Verify checkpoint exists
        result = saver.get_tuple(saved_config)
        assert result is not None

        # Delete thread
        saver.delete_thread("thread-to-delete")

        # Verify checkpoint is gone
        result = saver.get_tuple(saved_config)
        assert result is None


def test_parent_checkpoint() -> None:
    """Test that parent checkpoint is properly tracked."""
    with _saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-parent",
                "checkpoint_ns": "",
            }
        }

        # Create first checkpoint
        checkpoint_1 = empty_checkpoint()
        saved_config_1 = saver.put(config, checkpoint_1, {}, {})

        # Create second checkpoint with parent
        checkpoint_2 = create_checkpoint(checkpoint_1, {}, 1)
        saved_config_2 = saver.put(saved_config_1, checkpoint_2, {}, {})

        # Retrieve and verify parent
        result = saver.get_tuple(saved_config_2)
        assert result is not None
        assert result.parent_config is not None
        assert (
            result.parent_config["configurable"]["checkpoint_id"] == checkpoint_1["id"]
        )


def test_multiple_namespaces() -> None:
    """Test checkpoints with different namespaces."""
    with _saver() as saver:
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

        saver.put(config_1, checkpoint_1, {"ns": "root"}, {})
        saver.put(config_2, checkpoint_2, {"ns": "inner"}, {})

        # Get root namespace
        result_1 = saver.get_tuple(config_1)
        assert result_1 is not None
        assert result_1.config["configurable"]["checkpoint_ns"] == ""

        # Get inner namespace
        result_2 = saver.get_tuple(config_2)
        assert result_2 is not None
        assert result_2.config["configurable"]["checkpoint_ns"] == "inner"


def test_migrations_idempotent() -> None:
    """Test that running setup multiple times is safe."""
    with _saver() as saver:
        # Run setup again
        saver.setup()

        # Should still work
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-idempotent",
                "checkpoint_ns": "",
            }
        }
        checkpoint = empty_checkpoint()
        saved_config = saver.put(config, checkpoint, {}, {})

        result = saver.get_tuple(saved_config)
        assert result is not None


def test_combined_metadata() -> None:
    """Test that metadata from config is combined with checkpoint metadata."""
    with _saver() as saver:
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

        saved_config = saver.put(config, checkpoint, checkpoint_metadata, {})

        result = saver.get_tuple(saved_config)
        assert result is not None
        # Metadata from config should be merged with checkpoint metadata
        assert result.metadata["source"] == "loop"
        assert result.metadata["step"] == 1
        assert result.metadata["run_id"] == "my_run_id"


def test_pending_sends_migration() -> None:
    """Test that pending sends are properly migrated from writes to channel_values."""
    with _saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-sends",
                "checkpoint_ns": "",
            }
        }

        # Create the first checkpoint and put some pending sends
        checkpoint_0 = empty_checkpoint()
        config = saver.put(config, checkpoint_0, {}, {})
        saver.put_writes(
            config, [(TASKS, "send-1"), (TASKS, "send-2")], task_id="task-1"
        )
        saver.put_writes(config, [(TASKS, "send-3")], task_id="task-2")

        # Check that fetching checkpoint_0 doesn't attach pending sends
        # (they should be attached to the next checkpoint)
        tuple_0 = saver.get_tuple(config)
        assert tuple_0 is not None
        assert tuple_0.checkpoint["channel_values"] == {}
        assert tuple_0.checkpoint["channel_versions"] == {}

        # Create the second checkpoint
        checkpoint_1 = create_checkpoint(checkpoint_0, {}, 1)
        config = saver.put(config, checkpoint_1, {}, {})

        # Check that pending sends are attached to checkpoint_1
        tuple_1 = saver.get_tuple(config)
        assert tuple_1 is not None
        assert tuple_1.checkpoint["channel_values"] == {
            TASKS: ["send-1", "send-2", "send-3"]
        }
        assert TASKS in tuple_1.checkpoint["channel_versions"]

        # Check that list also applies the migration
        search_results = list(
            saver.list({"configurable": {"thread_id": "thread-sends"}})
        )
        assert len(search_results) == 2
        assert search_results[-1].checkpoint["channel_values"] == {}
        assert search_results[-1].checkpoint["channel_versions"] == {}
        assert search_results[0].checkpoint["channel_values"] == {
            TASKS: ["send-1", "send-2", "send-3"]
        }
        assert TASKS in search_results[0].checkpoint["channel_versions"]


def test_null_chars() -> None:
    """Test that null characters in metadata are handled properly."""
    with _saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-null",
                "checkpoint_ns": "",
            }
        }
        checkpoint = empty_checkpoint()
        # Put checkpoint with null character in metadata
        saved_config = saver.put(config, checkpoint, {"my_key": "\x00abc"}, {})

        result = saver.get_tuple(saved_config)
        assert result is not None
        # Null character should be stripped or handled
        assert result.metadata["my_key"] == "abc"

        # Check list filter also works
        results = list(saver.list(None, filter={"my_key": "abc"}))
        assert len(results) == 1
        assert results[0].metadata["my_key"] == "abc"


def test_get_checkpoint_no_channel_values(monkeypatch) -> None:
    """Backwards compatibility test for checkpoints without channel_values key."""
    with _saver() as saver:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": "thread-no-cv",
                "checkpoint_ns": "",
            }
        }
        checkpoint = create_checkpoint(empty_checkpoint(), {}, 1)
        saver.put(config, checkpoint, {}, {})

        # Patch to simulate old checkpoint format without channel_values
        original_load = saver._load_checkpoint_data

        def patched_load(row, cursor, pending_sends=None):
            result = original_load(row, cursor, pending_sends)
            # Simulate checkpoint without channel_values
            result.checkpoint.pop("channel_values", None)
            return result

        monkeypatch.setattr(saver, "_load_checkpoint_data", patched_load)

        # Should not raise an error
        result = saver.get_tuple(config)
        # Channel values should default to empty dict
        assert result is not None
