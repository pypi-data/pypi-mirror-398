"""Firestore-based checkpoint implementation for LangGraph."""

from __future__ import annotations

import asyncio
import logging
import typing
from typing import Any, AsyncIterator

from google.cloud import firestore
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    SerializerProtocol,
)

if typing.TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)


class FirestoreCheckpointer(BaseCheckpointSaver):
    """Firestore-backed checkpointer."""

    def __init__(
        self,
        client: firestore.Client,
        *,
        serde: SerializerProtocol | None = None,
    ) -> None:
        super().__init__(serde=serde)
        self.client = client

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict[str, str | int | float],
    ) -> RunnableConfig:
        """Save a checkpoint to Firestore."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]
        parent_checkpoint_id = config["configurable"].get("checkpoint_id")

        c_type, c_bytes = self.serde.dumps_typed(checkpoint)
        m_type, m_bytes = self.serde.dumps_typed(metadata)

        data = {
            "checkpoint": c_bytes,
            "checkpoint_type": c_type,
            "metadata": m_bytes,
            "metadata_type": m_type,
            "parent_checkpoint_id": parent_checkpoint_id,
            "ts": firestore.SERVER_TIMESTAMP,
        }

        ref = (
            self.client.collection("threads")
            .document(str(thread_id))
            .collection("checkpoints")
            .document(str(checkpoint_id))
        )
        await asyncio.to_thread(ref.set, data)

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
            }
        }

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: list[tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Save intermediate writes to Firestore."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"]["checkpoint_id"]

        batch = self.client.batch()
        writes_collection = (
            self.client.collection("threads")
            .document(str(thread_id))
            .collection("writes")
        )

        for idx, (channel, value) in enumerate(writes):
            doc_id = f"{checkpoint_id}_{task_id}_{idx}"
            ref = writes_collection.document(doc_id)
            type_, bytes_ = self.serde.dumps_typed(value)
            data = {
                "checkpoint_id": checkpoint_id,
                "task_id": task_id,
                "channel": channel,
                "value": bytes_,
                "type": type_,
                "idx": idx,
            }
            batch.set(ref, data)

        await asyncio.to_thread(batch.commit)

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Get a checkpoint tuple from Firestore."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id")

        checkpoints_ref = (
            self.client.collection("threads")
            .document(str(thread_id))
            .collection("checkpoints")
        )

        if checkpoint_id:
            doc = await asyncio.to_thread(
                checkpoints_ref.document(str(checkpoint_id)).get
            )
            if not doc.exists:
                print(f"DEBUG: aget_tuple checkpoint {checkpoint_id} not found")
                return None
        else:
            query = checkpoints_ref.order_by(
                "ts", direction=firestore.Query.DESCENDING
            ).limit(1)
            docs = await asyncio.to_thread(query.get)
            if not docs:
                print("DEBUG: aget_tuple no latest checkpoint found")
                return None
            doc = docs[0]
            checkpoint_id = doc.id

        print(f"DEBUG: aget_tuple found checkpoint {checkpoint_id}")            
        checkpoint_id = doc.id

        data = doc.to_dict()
        checkpoint = self.serde.loads_typed(
            (data.get("checkpoint_type", "json"), data["checkpoint"])
        )
        metadata = self.serde.loads_typed(
            (data.get("metadata_type", "json"), data["metadata"])
        )
        parent_checkpoint_id = data.get("parent_checkpoint_id")

        writes_ref = (
            self.client.collection("threads")
            .document(str(thread_id))
            .collection("writes")
        )
        query = writes_ref.where("checkpoint_id", "==", checkpoint_id)
        write_docs = await asyncio.to_thread(query.get)

        pending_writes = []
        for w_doc in write_docs:
            w_data = w_doc.to_dict()
            pending_writes.append(
                (
                    w_data["task_id"],
                    w_data["channel"],
                    self.serde.loads_typed(
                        (w_data.get("type", "json"), w_data["value"])
                    ),
                )
            )

        parent_config = None
        if parent_checkpoint_id:
            parent_config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": parent_checkpoint_id,
                }
            }

        return CheckpointTuple(
            config,
            checkpoint,
            metadata,
            parent_config,
            pending_writes,
        )

    async def alist(
        self,
        config: RunnableConfig,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """List checkpoints from Firestore."""
        thread_id = config["configurable"]["thread_id"]
        print(f"DEBUG: alist thread_id={thread_id} limit={limit} before={before}")
        query = (
            self.client.collection("threads")
            .document(str(thread_id))
            .collection("checkpoints")
            .order_by("ts", direction=firestore.Query.DESCENDING)
        )

        if before:
            before_id = before["configurable"].get("checkpoint_id")
            if before_id:
                doc = await asyncio.to_thread(
                    self.client.collection("threads")
                    .document(str(thread_id))
                    .collection("checkpoints")
                    .document(str(before_id))
                    .get
                )
                if doc.exists:
                    query = query.start_after(doc)

        if limit:
            query = query.limit(limit)

        docs = await asyncio.to_thread(query.get)

        writes_ref = (
            self.client.collection("threads")
            .document(str(thread_id))
            .collection("writes")
        )

        for doc in docs:
            data = doc.to_dict()
            checkpoint = self.serde.loads_typed(
                (data.get("checkpoint_type", "json"), data["checkpoint"])
            )
            metadata = self.serde.loads_typed(
                (data.get("metadata_type", "json"), data["metadata"])
            )
            parent_checkpoint_id = data.get("parent_checkpoint_id")

            w_query = writes_ref.where("checkpoint_id", "==", doc.id)
            w_docs = await asyncio.to_thread(w_query.get)
            pending_writes = [
                (
                    d.get("task_id"),
                    d.get("channel"),
                    self.serde.loads_typed((d.get("type", "json"), d.get("value"))),
                )
                for d in [wd.to_dict() for wd in w_docs]
            ]

            parent_config = None
            if parent_checkpoint_id:
                parent_config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_id": parent_checkpoint_id,
                    }
                }

            yield CheckpointTuple(
                {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_id": doc.id,
                    }
                },
                checkpoint,
                metadata,
                parent_config,
                pending_writes,
            )


def Checkpointer(conn=None, unpack_hook=None, **kwargs):
    """Get or create a Firestore checkpointer instance."""
    from langgraph_api.serde import Serializer
    from langgraph_runtime_firestore.database import initialize_firestore_cached

    serde = Serializer(__unpack_ext_hook__=unpack_hook) if unpack_hook else None

    if conn is not None:
        client = conn.db
    else:
        client = initialize_firestore_cached()

    return FirestoreCheckpointer(client, serde=serde)


__all__ = ["Checkpointer"]
