"""Firestore operations for LangGraph API.

This module implements CRUD operations for threads, runs, assistants, and crons
using Firestore as the backend storage.
"""

from __future__ import annotations

import asyncio
import base64
import copy
import json
import typing
import uuid
from collections import defaultdict
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, cast
from uuid import UUID, uuid4

import orjson
import structlog
from langgraph.checkpoint.serde.jsonplus import _msgpack_ext_hook_to_json
from langgraph.pregel.debug import CheckpointPayload
from langgraph.types import Interrupt, StateSnapshot
from langgraph.version import __version__
from langgraph_sdk import Auth
from starlette.exceptions import HTTPException

from langgraph_runtime_firestore.checkpoint import Checkpointer
from langgraph_runtime_firestore.database import FirestoreConnectionProto, connect
from langgraph_runtime_firestore.firestore_stream import (
    THREADLESS_KEY,
    ContextQueue,
    Message,
    get_stream_manager,
)
from langgraph_runtime_firestore.retry import retry_db
from langgraph_runtime_firestore.serialize import serialize_for_firestore

if typing.TYPE_CHECKING:
    from langgraph_api.asyncio import ValueEvent
    from langgraph_api.config import ThreadTTLConfig
    from langgraph_api.schema import (
        Assistant,
        AssistantSelectField,
        Checkpoint,
        Config,
        Context,
        DeprecatedInterrupt,
        IfNotExists,
        MetadataInput,
        MetadataValue,
        MultitaskStrategy,
        OnConflictBehavior,
        QueueStats,
        Run,
        RunSelectField,
        RunStatus,
        StreamMode,
        Thread,
        ThreadSelectField,
        ThreadStatus,
        ThreadStreamMode,
        ThreadUpdateResponse,
    )
    from langgraph_api.schema import Interrupt as InterruptSchema
    from langgraph_api.utils import AsyncConnectionProto

logger = structlog.stdlib.get_logger(__name__)

LANGGRAPH_PY_MINOR = tuple(map(int, __version__.split(".")[:2]))
USE_NEW_INTERRUPTS = LANGGRAPH_PY_MINOR >= (0, 6)


def _ensure_uuid(id_: str | uuid.UUID | None) -> uuid.UUID:
    """Ensure a value is a UUID."""
    if isinstance(id_, str):
        return uuid.UUID(id_)
    if id_ is None:
        return uuid4()
    return id_


def _get_username_from_ctx() -> str:
    """Extract username from auth context."""

    # Try global auth context
    from langgraph_api.utils import get_auth_ctx

    ctx = get_auth_ctx()
    if ctx:
        user = getattr(ctx, "user", None)
        if user:
            identity = (
                user.get("identity")
                if isinstance(user, dict)
                else getattr(user, "identity", None)
            )
            if identity:
                return identity

    raise HTTPException(status_code=401, detail="Authentication required")


def _snapshot_defaults():
    # Support older versions of langgraph
    if not hasattr(StateSnapshot, "interrupts"):
        return {}
    return {"interrupts": tuple()}


class WrappedHTTPException(Exception):
    def __init__(self, http_exception: HTTPException):
        self.http_exception = http_exception


class Authenticated:
    resource: Literal["threads", "crons", "assistants"]

    @classmethod
    def _context(
        cls,
        ctx: Auth.types.BaseAuthContext | None,
        action: Literal["create", "read", "update", "delete", "create_run"],
    ) -> Auth.types.AuthContext | None:
        if not ctx:
            return
        return Auth.types.AuthContext(
            user=ctx.user,
            permissions=ctx.permissions,
            resource=cls.resource,
            action=action,
        )

    @classmethod
    async def handle_event(
        cls,
        ctx: Auth.types.BaseAuthContext | None,
        action: Literal["create", "read", "update", "delete", "search", "create_run"],
        value: Any,
    ) -> Auth.types.FilterType | None:
        from langgraph_api.auth.custom import handle_event
        from langgraph_api.utils import get_auth_ctx

        ctx = ctx or get_auth_ctx()
        if not ctx:
            return
        return await handle_event(cls._context(ctx, action), value)


class Assistants(Authenticated):
    """Firestore-based Assistants operations."""

    resource = "assistants"

    @staticmethod
    async def search(
        conn: FirestoreConnectionProto,
        *,
        graph_id: str | None,
        metadata: MetadataInput,
        limit: int,
        offset: int,
        sort_by: str | None = None,
        sort_order: str | None = None,
        select: list[AssistantSelectField] | None = None,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> tuple[AsyncIterator[Assistant], int]:
        metadata = metadata if metadata is not None else {}
        filters = await Assistants.handle_event(
            ctx,
            "search",
            Auth.types.AssistantsSearch(
                graph_id=graph_id, metadata=metadata, limit=limit, offset=offset
            ),
        )

        # Get all assistants and filter them
        assistants = conn.store["assistants"]
        filtered_assistants = [
            assistant
            for assistant in assistants
            if (not graph_id or assistant["graph_id"] == graph_id)
            and (not metadata or is_jsonb_contained(assistant["metadata"], metadata))
            and (not filters or _check_filter_match(assistant["metadata"], filters))
        ]

        # Sort based on sort_by and sort_order
        sort_by = sort_by.lower() if sort_by else None
        if sort_by and sort_by in (
            "assistant_id",
            "graph_id",
            "name",
            "created_at",
            "updated_at",
        ):
            reverse = False if sort_order and sort_order.upper() == "ASC" else True
            # Use case-insensitive sorting for string fields
            if sort_by in ["name", "graph_id"]:
                filtered_assistants.sort(
                    key=lambda x: (
                        str(x.get(sort_by, "")).lower() if x.get(sort_by) else ""
                    ),
                    reverse=reverse,
                )
            else:
                filtered_assistants.sort(key=lambda x: x.get(sort_by), reverse=reverse)
        else:
            sort_by = "created_at"
            # Default sorting by created_at in descending order
            filtered_assistants.sort(key=lambda x: x["created_at"], reverse=True)

        # Apply pagination
        paginated_assistants = filtered_assistants[offset : offset + limit]
        cur = offset + limit if len(filtered_assistants) > offset + limit else None

        async def assistant_iterator() -> AsyncIterator[Assistant]:
            for assistant in paginated_assistants:
                if select:
                    # Filter to only selected fields
                    filtered_assistant = {
                        k: v for k, v in assistant.items() if k in select
                    }
                    yield filtered_assistant
                else:
                    yield assistant

        return assistant_iterator(), cur

    @staticmethod
    async def get(
        conn: FirestoreConnectionProto,
        assistant_id: UUID | str,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[Assistant]:
        """Get an assistant by ID."""
        assistant_id = _ensure_uuid(assistant_id)
        filters = await Assistants.handle_event(
            ctx,
            "read",
            Auth.types.AssistantsRead(assistant_id=assistant_id),
        )

        async def _yield_result():
            for assistant in conn.store["assistants"]:
                if assistant["assistant_id"] == assistant_id and (
                    not filters or _check_filter_match(assistant["metadata"], filters)
                ):
                    yield copy.deepcopy(assistant)

        return _yield_result()

    @staticmethod
    async def put(
        conn: FirestoreConnectionProto,
        assistant_id: UUID | str,
        *,
        graph_id: str,
        config: Config,
        context: Context,
        metadata: MetadataInput,
        if_exists: OnConflictBehavior,
        name: str,
        ctx: Auth.types.BaseAuthContext | None = None,
        description: str | None = None,
    ) -> AsyncIterator[Assistant]:
        """Insert an assistant."""
        from langgraph_api.graph import GRAPHS

        assistant_id = _ensure_uuid(assistant_id)
        metadata = metadata if metadata is not None else {}
        filters = await Assistants.handle_event(
            ctx,
            "create",
            Auth.types.AssistantsCreate(
                assistant_id=assistant_id,
                graph_id=graph_id,
                config=config,
                context=context,
                metadata=metadata,
                name=name,
            ),
        )

        if config.get("configurable") and context:
            raise HTTPException(
                status_code=400,
                detail="Cannot specify both configurable and context. Prefer setting context alone. Context was introduced in LangGraph 0.6.0 and is the long term planned replacement for configurable.",
            )

        if graph_id not in GRAPHS:
            raise HTTPException(status_code=404, detail=f"Graph {graph_id} not found")

        # Keep config and context up to date with one another
        if config.get("configurable"):
            context = config["configurable"]
        elif context:
            config["configurable"] = context

        existing_assistant = next(
            (a for a in conn.store["assistants"] if a["assistant_id"] == assistant_id),
            None,
        )
        if existing_assistant:
            if filters and not _check_filter_match(
                existing_assistant["metadata"], filters
            ):
                raise HTTPException(
                    status_code=409, detail=f"Assistant {assistant_id} already exists"
                )
            if if_exists == "raise":
                raise HTTPException(
                    status_code=409, detail=f"Assistant {assistant_id} already exists"
                )
            elif if_exists == "do_nothing":

                async def _yield_existing():
                    yield existing_assistant

                return _yield_existing()

        now = datetime.now(UTC)
        new_assistant: Assistant = {
            "assistant_id": assistant_id,
            "graph_id": graph_id,
            "config": config or {},
            "context": context or {},
            "metadata": metadata or {},
            "name": name,
            "created_at": now,
            "updated_at": now,
            "version": 1,
            "description": description,
        }
        new_version = {
            "assistant_id": assistant_id,
            "version": 1,
            "graph_id": graph_id,
            "config": config or {},
            "context": context or {},
            "metadata": metadata or {},
            "created_at": now,
            "name": name,
            "description": description,
        }
        conn.store["assistants"].append(new_assistant)
        conn.store["assistant_versions"].append(new_version)
        conn.db.collection("assistants").document(str(assistant_id)).set(
            serialize_for_firestore(new_assistant)
        )
        conn.db.collection("assistant_versions").document(f"{assistant_id}_v1").set(
            serialize_for_firestore(new_version)
        )

        async def _yield_new():
            yield new_assistant

        return _yield_new()

    @staticmethod
    async def patch(
        conn: FirestoreConnectionProto,
        assistant_id: UUID,
        *,
        config: Config | None = None,
        context: Context | None = None,
        graph_id: str | None = None,
        metadata: MetadataInput | None = None,
        name: str | None = None,
        description: str | None = None,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[Assistant]:
        """Update an assistant.

        Args:
            conn: The connection to the in-memory store.
            assistant_id: The assistant ID.
            graph_id: The graph ID.
            config: The assistant config.
            context: The assistant's static context.
            metadata: The assistant metadata.
            name: The assistant name.
            description: The assistant description.
            ctx: The auth context.

        Returns:
            return the updated assistant model.
        """
        assistant_id = _ensure_uuid(assistant_id)
        metadata = metadata if metadata is not None else {}
        config = config if config is not None else {}
        filters = await Assistants.handle_event(
            ctx,
            "update",
            Auth.types.AssistantsUpdate(
                assistant_id=assistant_id,
                graph_id=graph_id,
                config=config,
                context=context,
                metadata=metadata,
                name=name,
            ),
        )

        if config.get("configurable") and context:
            raise HTTPException(
                status_code=400,
                detail="Cannot specify both configurable and context. Prefer setting context alone. Context was introduced in LangGraph 0.6.0 and is the long term planned replacement for configurable.",
            )

        # Keep config and context up to date with one another
        if config.get("configurable"):
            context = config["configurable"]
        elif context:
            config["configurable"] = context

        assistant = next(
            (a for a in conn.store["assistants"] if a["assistant_id"] == assistant_id),
            None,
        )
        if not assistant:
            raise HTTPException(
                status_code=404, detail=f"Assistant {assistant_id} not found"
            )
        elif filters and not _check_filter_match(assistant["metadata"], filters):
            raise HTTPException(
                status_code=404, detail=f"Assistant {assistant_id} not found"
            )

        now = datetime.now(UTC)
        new_version = (
            max(
                v["version"]
                for v in conn.store["assistant_versions"]
                if v["assistant_id"] == assistant_id
            )
            + 1
            if conn.store["assistant_versions"]
            else 1
        )

        new_version_entry = {
            "assistant_id": assistant_id,
            "version": new_version,
            "graph_id": graph_id if graph_id is not None else assistant["graph_id"],
            "config": config if config else assistant["config"],
            "context": context if context is not None else assistant.get("context", {}),
            "metadata": (
                {**assistant["metadata"], **metadata}
                if metadata is not None
                else assistant["metadata"]
            ),
            "created_at": now,
            "name": name if name is not None else assistant["name"],
            "description": (
                description if description is not None else assistant.get("description")
            ),
        }
        conn.store["assistant_versions"].append(new_version_entry)
        conn.db.collection("assistant_versions").document(str(uuid.uuid4())).set(
            new_version_entry
        )

        # Update assistants table
        assistant.update(
            {
                "graph_id": new_version_entry["graph_id"],
                "config": new_version_entry["config"],
                "context": new_version_entry["context"],
                "metadata": new_version_entry["metadata"],
                "name": name if name is not None else assistant["name"],
                "description": (
                    description
                    if description is not None
                    else assistant.get("description")
                ),
                "updated_at": now,
                "version": new_version,
            }
        )

        async def _yield_updated():
            yield assistant

        return _yield_updated()

    @staticmethod
    async def delete(
        conn: FirestoreConnectionProto,
        assistant_id: UUID,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[UUID]:
        """Delete an assistant by ID."""
        assistant_id = _ensure_uuid(assistant_id)
        filters = await Assistants.handle_event(
            ctx,
            "delete",
            Auth.types.AssistantsDelete(
                assistant_id=assistant_id,
            ),
        )
        assistant = next(
            (a for a in conn.store["assistants"] if a["assistant_id"] == assistant_id),
            None,
        )

        if not assistant:
            raise HTTPException(
                status_code=404, detail=f"Assistant with ID {assistant_id} not found"
            )
        elif filters and not _check_filter_match(assistant["metadata"], filters):
            raise HTTPException(
                status_code=404, detail=f"Assistant with ID {assistant_id} not found"
            )

        conn.store["assistants"] = [
            a for a in conn.store["assistants"] if a["assistant_id"] != assistant_id
        ]
        # Cascade delete assistant versions, crons, & runs on this assistant
        conn.store["assistant_versions"] = [
            v
            for v in conn.store["assistant_versions"]
            if v["assistant_id"] != assistant_id
        ]
        conn.db.collection("assistants").document(str(assistant_id)).delete()
        # TODO: delete versions properly conn.db.collection("assistant_versions").where("assistant_id", "==", assistant_id).delete()
        retained = []
        for run in conn.store["runs"]:
            if run["assistant_id"] == assistant_id:
                res = await Runs.delete(
                    conn, run["run_id"], thread_id=run["thread_id"], ctx=ctx
                )
                await anext(res)
            else:
                retained.append(run)

        async def _yield_deleted():
            yield assistant_id

        return _yield_deleted()

    @staticmethod
    async def set_latest(
        conn: FirestoreConnectionProto,
        assistant_id: UUID,
        version: int,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[Assistant]:
        """Change the version of an assistant."""
        assistant_id = _ensure_uuid(assistant_id)
        filters = await Assistants.handle_event(
            ctx,
            "update",
            Auth.types.AssistantsUpdate(
                assistant_id=assistant_id,
                version=version,
            ),
        )
        assistant = next(
            (a for a in conn.store["assistants"] if a["assistant_id"] == assistant_id),
            None,
        )
        if not assistant:
            raise HTTPException(
                status_code=404, detail=f"Assistant {assistant_id} not found"
            )
        elif filters and not _check_filter_match(assistant["metadata"], filters):
            raise HTTPException(
                status_code=404, detail=f"Assistant {assistant_id} not found"
            )

        version_data = next(
            (
                v
                for v in conn.store["assistant_versions"]
                if v["assistant_id"] == assistant_id and v["version"] == version
            ),
            None,
        )
        if not version_data:
            raise HTTPException(
                status_code=404,
                detail=f"Version {version} not found for assistant {assistant_id}",
            )

        assistant.update(
            {
                "config": version_data["config"],
                "metadata": version_data["metadata"],
                "version": version_data["version"],
                "updated_at": datetime.now(UTC),
                "name": version_data["name"],
                "description": version_data["description"],
            }
        )

        assistant_ref = conn.db.collection("assistants").document(str(assistant_id))
        await asyncio.to_thread(assistant_ref.set, assistant)

        async def _yield_updated():
            yield assistant

        return _yield_updated()

    @staticmethod
    async def get_versions(
        conn: FirestoreConnectionProto,
        assistant_id: UUID,
        metadata: MetadataInput,
        limit: int,
        offset: int,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[Assistant]:
        """Get all versions of an assistant."""
        assistant_id = _ensure_uuid(assistant_id)
        filters = await Assistants.handle_event(
            ctx,
            "read",
            Auth.types.AssistantsRead(assistant_id=assistant_id),
        )
        assistant = next(
            (a for a in conn.store["assistants"] if a["assistant_id"] == assistant_id),
            None,
        )
        if not assistant:
            raise HTTPException(
                status_code=404, detail=f"Assistant {assistant_id} not found"
            )
        versions = [
            v
            for v in conn.store["assistant_versions"]
            if v["assistant_id"] == assistant_id
            and (not metadata or is_jsonb_contained(v["metadata"], metadata))
            and (not filters or _check_filter_match(v["metadata"], filters))
        ]

        # Previously, the name was not included in the assistant_versions table. So we should add them here.
        description = assistant.get("description")
        for v in versions:
            if "name" not in v:
                v["name"] = assistant["name"]
            if "description" not in v:
                v["description"] = description
            else:
                description = v["description"]

        versions.sort(key=lambda x: x["version"], reverse=True)

        async def _yield_versions():
            for version in versions[offset : offset + limit]:
                yield version

        return _yield_versions()

    @staticmethod
    async def count(
        conn: FirestoreConnectionProto,
        *,
        graph_id: str | None = None,
        metadata: MetadataInput = None,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> int:
        """Get count of assistants."""
        metadata = metadata if metadata is not None else {}
        filters = await Assistants.handle_event(
            ctx,
            "search",
            Auth.types.AssistantsSearch(
                graph_id=graph_id, metadata=metadata, limit=0, offset=0
            ),
        )

        count = 0
        for assistant in conn.store["assistants"]:
            if (
                (not graph_id or assistant["graph_id"] == graph_id)
                and (
                    not metadata or is_jsonb_contained(assistant["metadata"], metadata)
                )
                and (not filters or _check_filter_match(assistant["metadata"], filters))
            ):
                count += 1

        return count


def is_jsonb_contained(superset: dict[str, Any], subset: dict[str, Any]) -> bool:
    """
    Implements Postgres' @> (containment) operator for dictionaries.
    Returns True if superset contains all key/value pairs from subset.
    """
    for key, value in subset.items():
        if key not in superset:
            return False
        if isinstance(value, dict) and isinstance(superset[key], dict):
            if not is_jsonb_contained(superset[key], value):
                return False
        elif superset[key] != value:
            return False
    return True


def bytes_decoder(obj):
    """Custom JSON decoder that converts base64 back to bytes."""
    if "__type__" in obj and obj["__type__"] == "bytes":
        return base64.b64decode(obj["value"].encode("utf-8"))
    return obj


def _replace_thread_id(data, new_thread_id, thread_id):
    class BytesEncoder(json.JSONEncoder):
        """Custom JSON encoder that handles bytes by converting them to base64."""

        def default(self, obj):
            if isinstance(obj, bytes | bytearray):
                return {
                    "__type__": "bytes",
                    "value": base64.b64encode(
                        obj.replace(
                            str(thread_id).encode(), str(new_thread_id).encode()
                        )
                    ).decode("utf-8"),
                }

            return super().default(obj)


def _patch_interrupt(
    interrupt: Interrupt | dict,
) -> InterruptSchema | DeprecatedInterrupt:
    """Convert a langgraph interrupt (v0 or v1) to standard interrupt schema.

    In v0.4 and v0.5, interrupt_id is a property on the langgraph.types.Interrupt object,
    so we reconstruct the type in order to access the id, with compatibility for the new
    v0.6 interrupt format as well.
    """
    if USE_NEW_INTERRUPTS:
        interrupt = Interrupt(**interrupt) if isinstance(interrupt, dict) else interrupt

        return {
            "id": interrupt.id,
            "value": interrupt.value,
        }
    else:
        if isinstance(interrupt, dict):
            # interrupt_id is a deprecated property on Interrupt and should not be used for initialization
            # id is the new field we use for identification, also not supported on init for old versions
            interrupt.pop("interrupt_id", None)
            interrupt.pop("id", None)
            interrupt = Interrupt(**interrupt)

        return {
            "id": (
                interrupt.interrupt_id if hasattr(interrupt, "interrupt_id") else None
            ),
            "value": interrupt.value,
            "resumable": interrupt.resumable,
            "ns": interrupt.ns,
            "when": interrupt.when,  # type: ignore[unresolved-attribute]
        }


class Threads(Authenticated):
    resource = "threads"

    @staticmethod
    async def search(
        conn: FirestoreConnectionProto,
        *,
        ids: list[str] | list[UUID] | None = None,
        metadata: MetadataInput,
        values: MetadataInput,
        status: ThreadStatus | None,
        limit: int,
        offset: int,
        sort_by: str | None = None,
        sort_order: str | None = None,
        select: list[ThreadSelectField] | None = None,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> tuple[AsyncIterator[Thread], int]:
        metadata = metadata if metadata is not None else {}
        values = values if values is not None else {}

        username = _get_username_from_ctx()

        threads = conn.store["threads"].get(username, [])
        filtered_threads: list[Thread] = []
        filters = await Threads.handle_event(
            ctx,
            "search",
            Auth.types.ThreadsSearch(
                metadata=metadata,
                values=values,
                status=status,
                limit=limit,
                offset=offset,
            ),
        )

        # Apply filters
        id_set: set[UUID] | None = None
        if ids:
            id_set = set()
            for i in ids:
                try:
                    id_set.add(_ensure_uuid(i))
                except Exception:
                    raise HTTPException(
                        status_code=400, detail="Invalid thread ID " + str(i)
                    ) from None
        for thread in threads:
            if id_set is not None and thread.get("thread_id") not in id_set:
                continue
            if filters and not _check_filter_match(thread["metadata"], filters):
                continue

            if metadata and not is_jsonb_contained(thread["metadata"], metadata):
                continue

            if (
                values
                and "values" in thread
                and not is_jsonb_contained(thread["values"], values)
            ):
                continue

            if status and thread.get("status") != status:
                continue

            filtered_threads.append(thread)

        if sort_by and sort_by in [
            "thread_id",
            "created_at",
            "updated_at",
            "status",
        ]:
            reverse = False if sort_order and sort_order.upper() == "ASC" else True
            sorted_threads = sorted(
                filtered_threads, key=lambda x: x.get(sort_by), reverse=reverse
            )
        else:
            sort_by = "created_at"
            # Default sorting by created_at in descending order
            sorted_threads = sorted(
                filtered_threads, key=lambda x: x["updated_at"], reverse=True
            )

        # Apply limit and offset
        paginated_threads = sorted_threads[offset : offset + limit]
        cursor = offset + limit if len(sorted_threads) > offset + limit else None

        async def thread_iterator() -> AsyncIterator[Thread]:
            for thread in paginated_threads:
                if select:
                    # Filter to only selected fields
                    filtered_thread = {k: v for k, v in thread.items() if k in select}
                    yield filtered_thread
                else:
                    yield thread

        return thread_iterator(), cursor

    @staticmethod
    async def _get_with_filters(
        conn: FirestoreConnectionProto,
        thread_id: UUID,
        filters: Auth.types.FilterType | None,
        username: str | None = None,
    ) -> Thread | None:
        thread_id = _ensure_uuid(thread_id)

        if not username:
            return None

        matching_thread = next(
            (
                thread
                for thread in conn.store["threads"].get(username, [])
                if thread["thread_id"] == thread_id
            ),
            None,
        )
        if not matching_thread or (
            filters and not _check_filter_match(matching_thread["metadata"], filters)
        ):
            return

        return matching_thread

    @staticmethod
    async def _get(
        conn: FirestoreConnectionProto,
        thread_id: UUID,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> Thread | None:
        """Get a thread by ID."""
        thread_id = _ensure_uuid(thread_id)
        username = _get_username_from_ctx()
        filters = await Threads.handle_event(
            ctx,
            "read",
            Auth.types.ThreadsRead(thread_id=thread_id),
        )
        return await Threads._get_with_filters(conn, thread_id, filters, username)

    @staticmethod
    async def get(
        conn: FirestoreConnectionProto,
        thread_id: UUID,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[Thread]:
        """Get a thread by ID."""
        matching_thread = await Threads._get(conn, thread_id, ctx)

        if not matching_thread:
            raise HTTPException(
                status_code=404, detail=f"Thread with ID {thread_id} not found"
            )

        async def _yield_result():
            if matching_thread:
                yield matching_thread

        return _yield_result()

    @staticmethod
    async def put(
        conn: FirestoreConnectionProto,
        thread_id: UUID | str,
        *,
        metadata: MetadataInput,
        if_exists: OnConflictBehavior,
        ttl: ThreadTTLConfig | None = None,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[Thread]:
        """Insert or update a thread."""
        thread_id = _ensure_uuid(thread_id)
        if metadata is None:
            metadata = {}

        username = _get_username_from_ctx()

        # Check if thread already exists
        existing_thread = next(
            (
                t
                for t in conn.store["threads"].get(username, [])
                if t["thread_id"] == thread_id
            ),
            None,
        )
        filters = await Threads.handle_event(
            ctx,
            "create",
            Auth.types.ThreadsCreate(
                thread_id=thread_id, metadata=metadata, if_exists=if_exists
            ),
        )

        if existing_thread:
            if filters and not _check_filter_match(
                existing_thread["metadata"], filters
            ):
                raise HTTPException(
                    status_code=409, detail=f"Thread with ID {thread_id} already exists"
                )
            if if_exists == "raise":
                raise HTTPException(
                    status_code=409, detail=f"Thread with ID {thread_id} already exists"
                )
            elif if_exists == "do_nothing":

                async def _yield_existing():
                    yield existing_thread

                return _yield_existing()
        # Create new thread
        new_thread: Thread = {
            "thread_id": thread_id,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "metadata": copy.deepcopy(metadata),
            "status": "idle",
            "config": {},
            "values": None,
        }

        # Add to store
        conn.store["threads"].setdefault(username, []).append(new_thread)
        await asyncio.to_thread(
            conn.db.collection("users")
            .document(username)
            .collection("threads")
            .document(str(thread_id))
            .set,
            serialize_for_firestore(new_thread),
        )

        async def _yield_new():
            yield new_thread

        return _yield_new()

    @staticmethod
    async def patch(
        conn: FirestoreConnectionProto,
        thread_id: UUID,
        *,
        metadata: MetadataValue,
        ttl: ThreadTTLConfig | None = None,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[Thread]:
        """Update a thread."""
        thread_id = _ensure_uuid(thread_id)

        username = _get_username_from_ctx()

        threads = conn.store["threads"].get(username, [])
        thread_idx = None

        for idx, thread in enumerate(threads):
            if thread["thread_id"] == thread_id:
                thread_idx = idx
                break

        if thread_idx is not None:
            filters = await Threads.handle_event(
                ctx,
                "update",
                Auth.types.ThreadsUpdate(thread_id=thread_id, metadata=metadata),
            )
            if not filters or _check_filter_match(
                threads[thread_idx]["metadata"], filters
            ):
                thread = copy.deepcopy(threads[thread_idx])
                thread["metadata"] = {**thread["metadata"], **metadata}
                thread["updated_at"] = datetime.now(UTC)
                threads[thread_idx] = thread

                # Persist to Firestore
                thread_ref = (
                    conn.db.collection("users")
                    .document(username)
                    .collection("threads")
                    .document(str(thread_id))
                )
                await asyncio.to_thread(
                    thread_ref.set, serialize_for_firestore(thread), merge=True
                )

                async def thread_iterator() -> AsyncIterator[Thread]:
                    yield thread

                return thread_iterator()

        async def empty_iterator() -> AsyncIterator[Thread]:
            if False:  # This ensures the iterator is empty
                yield

        return empty_iterator()

    @staticmethod
    async def set_status(
        conn: FirestoreConnectionProto,
        thread_id: UUID,
        ctx: Auth.types.BaseAuthContext | None = None,
        checkpoint: CheckpointPayload | None = None,
        exception: BaseException | None = None,
    ) -> None:
        """Set the status of a thread."""
        from langgraph_api.serde import json_dumpb

        thread_id = _ensure_uuid(thread_id)
        username = _get_username_from_ctx()

        async def has_pending_runs(conn_: FirestoreConnectionProto, tid: UUID) -> bool:
            """Check if thread has any pending runs."""
            return any(
                run["status"] in ("pending", "running") and run["thread_id"] == tid
                for run in conn_.store["runs"]
            )

        # Find the thread in user's threads
        threads = conn.store["threads"].get(username, [])
        thread = next(
            (thread for thread in threads if thread["thread_id"] == thread_id),
            None,
        )

        if not thread:
            raise HTTPException(
                status_code=404, detail=f"Thread {thread_id} not found."
            )

        # Determine has_next from checkpoint
        has_next = False if checkpoint is None else bool(checkpoint["next"])

        # Determine base status
        if exception:
            status = "error"
        elif has_next:
            status = "interrupted"
        else:
            status = "idle"

        # Check for pending runs and update to busy if found
        if await has_pending_runs(conn, thread_id):
            status = "busy"

        # Update thread
        thread.update(
            {
                "updated_at": datetime.now(UTC),
                "values": checkpoint["values"] if checkpoint else None,
                "status": status,
                "interrupts": (
                    {
                        t["id"]: [_patch_interrupt(i) for i in t["interrupts"]]
                        for t in checkpoint["tasks"]
                        if t.get("interrupts")
                    }
                    if checkpoint
                    else {}
                ),
                "error": json_dumpb(exception) if exception else None,
            }
        )

        # Persist to Firestore
        thread_ref = (
            conn.db.collection("users")
            .document(username)
            .collection("threads")
            .document(str(thread_id))
        )
        await asyncio.to_thread(
            thread_ref.set, serialize_for_firestore(thread), merge=True
        )

    @staticmethod
    async def delete(
        conn: FirestoreConnectionProto,
        thread_id: UUID | str,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[UUID]:
        """Delete a thread by ID and cascade delete all associated runs.

        Args:
            conn: Database connection
            thread_id: Thread ID to delete
            ctx: Auth context

        Yields:
            Deleted thread ID
        """
        thread_id = _ensure_uuid(thread_id)
        username = _get_username_from_ctx()

        threads = conn.store["threads"].get(username, [])
        thread_idx = None
        thread = None

        # Find the thread to delete
        for idx, t in enumerate(threads):
            if t["thread_id"] == thread_id:
                thread_idx = idx
                thread = t
                break

        filters = await Threads.handle_event(
            ctx,
            "delete",
            Auth.types.ThreadsDelete(thread_id=thread_id),
        )

        if thread is None or (
            filters and not _check_filter_match(thread["metadata"], filters)
        ):
            raise HTTPException(
                status_code=404, detail=f"Thread with ID {thread_id} not found"
            )

        # Cascade delete all runs associated with this thread
        conn.store["runs"] = [
            run for run in conn.store["runs"] if run["thread_id"] != thread_id
        ]

        if thread_idx is not None:
            # Remove the thread from the store
            deleted_thread = threads.pop(thread_idx)

            # Delete from Firestore
            thread_ref = (
                conn.db.collection("users")
                .document(username)
                .collection("threads")
                .document(str(thread_id))
            )
            await asyncio.to_thread(thread_ref.delete)

            # Return an async iterator with the deleted thread_id
            async def id_iterator() -> AsyncIterator[UUID]:
                yield deleted_thread["thread_id"]

            return id_iterator()

        # If thread not found, return empty iterator
        async def empty_iterator() -> AsyncIterator[UUID]:
            if False:  # This ensures the iterator is empty
                yield

        return empty_iterator()

    @staticmethod
    async def set_joint_status(
        conn: FirestoreConnectionProto,
        thread_id: UUID,
        run_id: UUID,
        run_status: RunStatus | Literal["rollback"],
        graph_id: str,
        checkpoint: CheckpointPayload | None = None,
        exception: BaseException | None = None,
    ) -> None:
        """Set the status of both thread and run atomically in a single query.

        This is an optimized version that combines the logic from Threads.set_status
        and Runs.set_status to minimize database round trips and ensure atomicity.

        Args:
            conn: Database connection
            thread_id: Thread ID to update
            run_id: Run ID to update
            metadata: Metadata containing username for thread lookup
            run_status: New status for the run (or "rollback" to delete the run)
            checkpoint: Checkpoint payload for thread status calculation
            exception: Exception that occurred (affects thread status)
        """
        # No auth since it's internal
        from langgraph_api.errors import UserInterrupt, UserRollback
        from langgraph_api.serde import json_dumpb

        thread_id = _ensure_uuid(thread_id)
        run_id = _ensure_uuid(run_id)

        username = _get_username_from_ctx()

        def _thread_has_active_runs() -> bool:
            return any(
                r["thread_id"] == thread_id and r["status"] in ("pending", "running")
                for r in conn.store["runs"]
            )

        thread = next(
            (
                t
                for t in conn.store["threads"].get(username, [])
                if t["thread_id"] == thread_id
            ),
            None,
        )
        if thread is None:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

        run = next(
            (
                r
                for r in conn.store["runs"]
                if r["run_id"] == run_id and r["thread_id"] == thread_id
            ),
            None,
        )
        if run is None:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

        has_next = bool(checkpoint and checkpoint["next"])
        if exception and not isinstance(exception, UserInterrupt | UserRollback):
            base_thread_status: ThreadStatus = "error"
        elif has_next:
            base_thread_status = "interrupted"
        else:
            base_thread_status = "idle"

        interrupts = (
            {
                t["id"]: [_patch_interrupt(i) for i in t["interrupts"]]
                for t in checkpoint["tasks"]
                if t.get("interrupts")
            }
            if checkpoint
            else {}
        )

        now = datetime.now(UTC)

        if run_status == "rollback":
            await Runs.delete(conn, run_id, thread_id=run["thread_id"])
            final_thread_status: ThreadStatus = (
                "busy" if _thread_has_active_runs() else base_thread_status
            )

        else:
            run.update({"status": run_status, "updated_at": now})

            if run_status in ("pending", "running") or _thread_has_active_runs():
                final_thread_status = "busy"
            else:
                final_thread_status = base_thread_status
        thread["metadata"]["graph_id"] = graph_id
        thread.update(
            {
                "updated_at": now,
                "values": checkpoint["values"] if checkpoint else None,
                "interrupts": interrupts,
                "status": final_thread_status,
                "error": json_dumpb(exception) if exception else None,
            }
        )

        # Persist to Firestore
        thread_ref = (
            conn.db.collection("users")
            .document(username)
            .collection("threads")
            .document(str(thread_id))
        )
        print(thread)
        await asyncio.to_thread(
            thread_ref.set, serialize_for_firestore(thread), merge=True
        )

    @staticmethod
    async def _delete_with_run(
        conn: FirestoreConnectionProto,
        thread_id: UUID,
        run_id: UUID,
    ) -> UUID:
        """Delete a thread by ID."""
        # We don't really care about "optimal" here.
        run = next(
            (r for r in conn.store["runs"] if r["run_id"] == run_id),
            None,
        )

        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        metadata = run.get("metadata", {})
        return await Threads.delete(conn, thread_id, metadata=metadata)

    @staticmethod
    async def copy(
        conn: FirestoreConnectionProto,
        thread_id: UUID | str,
        metadata: MetadataInput | None = None,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[Thread]:
        """Create a copy of an existing thread.

        Args:
            conn: Database connection
            thread_id: Source thread ID
            metadata: Metadata containing username for thread lookup
            ctx: Auth context

        Yields:
            Copied thread
        """
        thread_id = _ensure_uuid(thread_id)
        new_thread_id = uuid4()

        username = metadata.get("username") if metadata else None
        if not username:
            raise HTTPException(status_code=400, detail="Metadata username is required")

        read_filters = await Threads.handle_event(
            ctx,
            "read",
            Auth.types.ThreadsRead(
                thread_id=thread_id,
            ),
        )
        # Assert that the user has permissions to create a new thread.
        # (We don't actually need the filters.)
        await Threads.handle_event(
            ctx,
            "create",
            Auth.types.ThreadsCreate(
                thread_id=new_thread_id,
            ),
        )

        # Find the original thread in user's threads
        threads = conn.store["threads"].get(username, [])
        original_thread = next(
            (t for t in threads if t["thread_id"] == thread_id), None
        )

        if not original_thread:

            async def empty_iterator() -> AsyncIterator[Thread]:
                if False:
                    yield

            return empty_iterator()

        if read_filters and not _check_filter_match(
            original_thread["metadata"], read_filters
        ):

            async def empty_iterator2() -> AsyncIterator[Thread]:
                if False:
                    yield

            return empty_iterator2()

        # Create new thread with copied metadata
        new_thread: Thread = {
            "thread_id": new_thread_id,
            "created_at": datetime.now(tz=UTC),
            "updated_at": datetime.now(tz=UTC),
            "metadata": copy.deepcopy(original_thread["metadata"]),
            "status": "idle",
            "config": {},
            "values": original_thread.get("values"),
        }

        # Add new thread to store in user's thread collection
        threads.append(new_thread)

        # Persist to Firestore
        thread_ref = (
            conn.db.collection("users")
            .document(username)
            .collection("threads")
            .document(str(new_thread_id))
        )
        await asyncio.to_thread(thread_ref.set, serialize_for_firestore(new_thread))

        async def row_generator() -> AsyncIterator[Thread]:
            yield new_thread

        return row_generator()

    @staticmethod
    async def sweep_ttl(
        conn: FirestoreConnectionProto,
        *,
        limit: int | None = None,
        batch_size: int = 100,
    ) -> tuple[int, int]:
        # Not implemented for Firestore server
        return (0, 0)

    class State:
        """State management for threads."""

        @staticmethod
        async def get(
            conn: FirestoreConnectionProto,
            config: Config,
            subgraphs: bool = False,
            ctx: Auth.types.BaseAuthContext | None = None,
        ) -> StateSnapshot:
            """Get state for a thread."""
            from langgraph_api.graph import get_graph
            from langgraph_api.store import get_store

            checkpointer = await asyncio.to_thread(
                Checkpointer, conn, unpack_hook=_msgpack_ext_hook_to_json
            )
            thread_id = _ensure_uuid(config["configurable"]["thread_id"])

            # Get thread with username-based lookup
            thread_iter = await Threads.get(conn, thread_id, ctx=ctx)
            thread = await anext(thread_iter, None)
            checkpoint = await checkpointer.aget(config)

            if not thread:
                return StateSnapshot(
                    values={},
                    next=[],
                    config=None,
                    metadata=None,
                    created_at=None,
                    parent_config=None,
                    tasks=tuple(),
                    **_snapshot_defaults(),
                )

            metadata = thread.get("metadata", {})
            thread_config = cast(dict[str, Any], thread.get("config", {}))
            thread_config = {
                **thread_config,
                "configurable": {
                    **thread_config.get("configurable", {}),
                    **config.get("configurable", {}),
                },
            }

            # Fallback to graph_id from run if not in thread metadata
            graph_id = metadata.get("graph_id")
            if not graph_id:
                for run in conn.store["runs"]:
                    if run["thread_id"] == thread_id:
                        graph_id = run["kwargs"]["config"]["configurable"]["graph_id"]
                        break

            if graph_id:
                # format latest checkpoint for response
                checkpointer.latest_iter = checkpoint
                async with get_graph(
                    graph_id,
                    thread_config,
                    checkpointer=checkpointer,
                    store=(await get_store()),
                ) as graph:
                    result = await graph.aget_state(config, subgraphs=subgraphs)
                    if (
                        result.metadata is not None
                        and "checkpoint_ns" in result.metadata
                        and result.metadata["checkpoint_ns"] == ""
                    ):
                        result.metadata.pop("checkpoint_ns")
                    return result
            else:
                return StateSnapshot(
                    values={},
                    next=[],
                    config=None,
                    metadata=None,
                    created_at=None,
                    parent_config=None,
                    tasks=tuple(),
                    **_snapshot_defaults(),
                )

        @staticmethod
        async def post(
            conn: FirestoreConnectionProto,
            config: Config,
            values: Sequence[dict] | dict[str, Any] | None = None,
            as_node: str | None = None,
            ctx: Auth.types.BaseAuthContext | None = None,
        ) -> ThreadUpdateResponse:
            """Add state to a thread."""
            from langgraph_api.graph import get_graph
            from langgraph_api.schema import ThreadUpdateResponse
            from langgraph_api.state import state_snapshot_to_thread_state
            from langgraph_api.store import get_store

            thread_id = _ensure_uuid(config["configurable"]["thread_id"])

            username = _get_username_from_ctx()

            filters = await Threads.handle_event(
                ctx,
                "update",
                Auth.types.ThreadsUpdate(thread_id=thread_id),
            )

            checkpointer = await asyncio.to_thread(
                Checkpointer, conn, unpack_hook=_msgpack_ext_hook_to_json
            )

            # Get thread with username-based lookup
            thread_iter = await Threads.get(conn, thread_id, ctx=ctx)
            thread = await anext(thread_iter, None)
            checkpoint = await checkpointer.aget(config)

            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            if filters and not _check_filter_match(thread["metadata"], filters):
                raise HTTPException(status_code=403, detail="Forbidden")

            metadata = thread["metadata"]
            thread_config = thread.get("config", {})

            # Check that there are no in-flight runs
            pending_runs = [
                run
                for run in conn.store["runs"]
                if run["thread_id"] == thread_id
                and run["status"] in ("pending", "running")
            ]
            if pending_runs:
                raise HTTPException(
                    status_code=409,
                    detail=f"Thread {thread_id} has in-flight runs: {pending_runs}",
                )

            thread_config = {
                **thread_config,
                "configurable": {
                    **thread_config.get("configurable", {}),
                    **config.get("configurable", {}),
                },
            }

            # Fallback to graph_id from run if not in thread metadata
            graph_id = metadata.get("graph_id")
            if not graph_id:
                for run in conn.store["runs"]:
                    if run["thread_id"] == thread_id:
                        graph_id = run["kwargs"]["config"]["configurable"]["graph_id"]
                        break

            if graph_id:
                config["configurable"].setdefault("graph_id", graph_id)

                checkpointer.latest_iter = checkpoint
                async with get_graph(
                    graph_id,
                    thread_config,
                    checkpointer=checkpointer,
                    store=(await get_store()),
                ) as graph:
                    update_config = config.copy()
                    update_config["configurable"] = {
                        **config["configurable"],
                        "checkpoint_ns": config["configurable"].get(
                            "checkpoint_ns", ""
                        ),
                    }
                    next_config = await graph.aupdate_state(
                        update_config, values, as_node=as_node
                    )

                    # Get current state
                    state = await Threads.State.get(
                        conn, config, subgraphs=False, ctx=ctx
                    )

                    # Update thread values in memory store
                    threads = conn.store["threads"].get(username, [])
                    for thread_in_store in threads:
                        if thread_in_store["thread_id"] == thread_id:
                            thread_in_store["values"] = state.values
                            break

                    # Persist to Firestore
                    thread_ref = (
                        conn.db.collection("users")
                        .document(username)
                        .collection("threads")
                        .document(str(thread_id))
                    )
                    await asyncio.to_thread(
                        thread_ref.update,
                        {
                            "values": state.values,
                            "updated_at": datetime.now(UTC),
                        },
                    )

                    # Publish state update event
                    from langgraph_api.serde import json_dumpb

                    event_data = {
                        "state": state_snapshot_to_thread_state(state),
                        "thread_id": str(thread_id),
                    }
                    await Threads.Stream.publish(
                        thread_id,
                        "state_update",
                        json_dumpb(event_data),
                    )

                    return ThreadUpdateResponse(
                        checkpoint=next_config["configurable"],
                        # Including deprecated fields
                        configurable=next_config["configurable"],
                        checkpoint_id=next_config["configurable"]["checkpoint_id"],
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Thread '{thread['thread_id']}' has no assigned graph ID. This usually occurs when no runs have been made on this particular thread."
                    " This operation requires a graph ID. Please ensure a run has been made for the thread or manually update the thread metadata (by setting the 'graph_id' field) before running this operation.",
                )

        @staticmethod
        async def bulk(
            conn: FirestoreConnectionProto,
            *,
            config: Config,
            supersteps: Sequence[dict],
            ctx: Auth.types.BaseAuthContext | None = None,
        ) -> ThreadUpdateResponse:
            """Update a thread with a batch of state updates."""

            from langgraph.types import StateUpdate
            from langgraph_api.command import map_cmd
            from langgraph_api.graph import get_graph
            from langgraph_api.schema import ThreadUpdateResponse
            from langgraph_api.state import state_snapshot_to_thread_state
            from langgraph_api.store import get_store

            thread_id = _ensure_uuid(config["configurable"]["thread_id"])

            username = _get_username_from_ctx()

            filters = await Threads.handle_event(
                ctx,
                "update",
                Auth.types.ThreadsUpdate(thread_id=thread_id),
            )

            # Get thread with username-based lookup
            thread_iter = await Threads.get(conn, thread_id, ctx=ctx)
            thread = await anext(thread_iter, None)

            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")

            if filters and not _check_filter_match(thread["metadata"], filters):
                raise HTTPException(status_code=403, detail="Forbidden")

            thread_config = cast(dict[str, Any], thread.get("config", {}))
            thread_config = {
                **thread_config,
                "configurable": {
                    **thread_config.get("configurable", {}),
                    **config.get("configurable", {}),
                },
            }
            metadata = thread["metadata"]

            if graph_id := metadata.get("graph_id"):
                config["configurable"].setdefault("graph_id", graph_id)
                config["configurable"].setdefault("checkpoint_ns", "")

                checkpointer = await asyncio.to_thread(
                    Checkpointer, conn, unpack_hook=_msgpack_ext_hook_to_json
                )
                async with get_graph(
                    graph_id,
                    thread_config,
                    checkpointer=checkpointer,
                    store=(await get_store()),
                ) as graph:
                    next_config = await graph.abulk_update_state(
                        config,
                        [
                            [
                                StateUpdate(
                                    (
                                        map_cmd(update.get("command"))
                                        if update.get("command")
                                        else update.get("values")
                                    ),
                                    update.get("as_node"),
                                )
                                for update in superstep.get("updates", [])
                            ]
                            for superstep in supersteps
                        ],
                    )

                    # Get current state
                    state = await Threads.State.get(
                        conn, config, subgraphs=False, ctx=ctx
                    )

                    # Update thread values in memory store
                    threads = conn.store["threads"].get(username, [])
                    for thread_in_store in threads:
                        if thread_in_store["thread_id"] == thread_id:
                            thread_in_store["values"] = state.values
                            break

                    # Persist to Firestore
                    thread_ref = (
                        conn.db.collection("users")
                        .document(username)
                        .collection("threads")
                        .document(str(thread_id))
                    )
                    await asyncio.to_thread(
                        thread_ref.update,
                        {
                            "values": state.values,
                            "updated_at": datetime.now(UTC),
                        },
                    )

                    # Publish state update event
                    from langgraph_api.serde import json_dumpb

                    event_data = {
                        "state": state_snapshot_to_thread_state(state),
                        "thread_id": str(thread_id),
                    }
                    await Threads.Stream.publish(
                        thread_id,
                        "state_update",
                        json_dumpb(event_data),
                    )

                    return ThreadUpdateResponse(
                        checkpoint=next_config["configurable"],
                        configurable=next_config["configurable"],
                        checkpoint_id=next_config["configurable"]["checkpoint_id"],
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Thread '{thread['thread_id']}' has no assigned graph ID. This usually occurs when no runs have been made on this particular thread."
                    " This operation requires a graph ID. Please ensure a run has been made for the thread or manually update the thread metadata (by setting the 'graph_id' field) before running this operation.",
                )

        @staticmethod
        async def list(
            conn: FirestoreConnectionProto,
            *,
            config: Config,
            limit: int = 1,
            before: str | Checkpoint | None = None,
            metadata: MetadataInput = None,
            ctx: Auth.types.BaseAuthContext | None = None,
        ) -> list[StateSnapshot]:
            """Get the history of a thread."""
            from langgraph_api.graph import get_graph
            from langgraph_api.store import get_store

            thread_id = _ensure_uuid(config["configurable"]["thread_id"])

            filters = await Threads.handle_event(
                ctx,
                "read",
                Auth.types.ThreadsRead(thread_id=thread_id),
            )

            # Get thread with username-based lookup
            thread_iter = await Threads.get(conn, thread_id, ctx=ctx)
            thread = await anext(thread_iter, None)

            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")

            # Parse thread metadata and config
            thread_metadata = thread["metadata"]
            if filters and not _check_filter_match(thread_metadata, filters):
                return []

            thread_config = cast(dict[str, Any], thread.get("config", {}))
            thread_config = {
                **thread_config,
                "configurable": {
                    **thread_config.get("configurable", {}),
                    **config.get("configurable", {}),
                },
            }
            # If graph_id exists, get state history
            if graph_id := thread_metadata.get("graph_id"):
                checkpointer = await asyncio.to_thread(
                    Checkpointer, conn, unpack_hook=_msgpack_ext_hook_to_json
                )
                async with get_graph(
                    graph_id,
                    thread_config,
                    checkpointer=checkpointer,
                    store=(await get_store()),
                ) as graph:
                    # Convert before parameter if it's a string
                    before_param = (
                        {"configurable": {"checkpoint_id": before}}
                        if isinstance(before, str)
                        else before
                    )

                    states = [
                        state
                        async for state in graph.aget_state_history(
                            config, limit=limit, filter=metadata, before=before_param
                        )
                    ]

                    return states

            return []

    class Stream:
        """Stream management for threads."""

        @staticmethod
        async def subscribe(
            conn: FirestoreConnectionProto | AsyncConnectionProto,
            thread_id: UUID,
            seen_runs: set[UUID],
        ) -> list[tuple[UUID, asyncio.Queue]]:
            """Subscribe to the thread stream, creating queues for unseen runs."""
            stream_manager = get_stream_manager()
            queues = []

            # Create new queues only for runs not yet seen
            thread_id = _ensure_uuid(thread_id)

            # Add thread stream queue
            if thread_id not in seen_runs:
                queue = await stream_manager.add_thread_stream(thread_id)
                queues.append((thread_id, queue))
                seen_runs.add(thread_id)

            for run in conn.store["runs"]:
                if run["thread_id"] == thread_id:
                    run_id = run["run_id"]
                    if run_id not in seen_runs:
                        queue = await stream_manager.add_queue(run_id, thread_id)
                        queues.append((run_id, queue))
                        seen_runs.add(run_id)

            return queues

        @staticmethod
        async def join(
            thread_id: UUID,
            *,
            last_event_id: str | None = None,
            stream_modes: list[ThreadStreamMode],
            ctx: Auth.types.BaseAuthContext | None = None,
        ) -> AsyncIterator[tuple[bytes, bytes, bytes | None]]:
            """Stream the thread output."""
            await Threads.Stream.check_thread_stream_auth(thread_id, ctx)

            from langgraph_api.utils.stream_codec import (
                decode_stream_message,
            )

            def should_filter_event(event_name: str, message_bytes: bytes) -> bool:
                """Check if an event should be filtered out based on stream_modes."""
                if "run_modes" in stream_modes and event_name != "state_update":
                    return False
                if "state_update" in stream_modes and event_name == "state_update":
                    return False
                if "lifecycle" in stream_modes and event_name == "metadata":
                    try:
                        message_data = orjson.loads(message_bytes)
                        if message_data.get("status") == "run_done":
                            return False
                        if "attempt" in message_data and "run_id" in message_data:
                            return False
                    except (orjson.JSONDecodeError, TypeError):
                        pass
                return True

            stream_manager = get_stream_manager()
            seen_runs: set[UUID] = set()
            created_queues: list[tuple[UUID, asyncio.Queue]] = []

            try:
                async with connect() as conn:
                    await logger.ainfo(
                        "Joined thread stream",
                        thread_id=str(thread_id),
                    )

                    # Restore messages if resuming from a specific event
                    if last_event_id is not None:
                        # Collect all events from all message stores for this thread
                        all_events = []
                        for run_id in stream_manager.message_stores.get(
                            str(thread_id), []
                        ):
                            for message in stream_manager.restore_messages(
                                run_id, thread_id, last_event_id
                            ):
                                all_events.append((message, run_id))

                        # Sort by message ID (which is ms-seq format)
                        all_events.sort(key=lambda x: x[0].id.decode())

                        # Yield sorted events
                        for message, run_id in all_events:
                            decoded = decode_stream_message(
                                message.data, channel=message.topic
                            )
                            event_bytes = decoded.event_bytes
                            message_bytes = decoded.message_bytes

                            if event_bytes == b"control":
                                if message_bytes == b"done":
                                    event_bytes = b"metadata"
                                    message_bytes = orjson.dumps(
                                        {"status": "run_done", "run_id": run_id}
                                    )
                            if not should_filter_event(
                                event_bytes.decode("utf-8"), message_bytes
                            ):
                                yield (
                                    event_bytes,
                                    message_bytes,
                                    message.id,
                                )

                    # Listen for live messages from all queues
                    while True:
                        # Refresh queues to pick up any new runs that joined this thread
                        new_queue_tuples = await Threads.Stream.subscribe(
                            conn, thread_id, seen_runs
                        )
                        # Track new queues for cleanup
                        for run_id, queue in new_queue_tuples:
                            created_queues.append((run_id, queue))

                        for run_id, queue in created_queues:
                            try:
                                message = await asyncio.wait_for(
                                    queue.get(), timeout=0.2
                                )
                                decoded = decode_stream_message(
                                    message.data, channel=message.topic
                                )
                                event = decoded.event_bytes
                                event_name = event.decode("utf-8")
                                payload = decoded.message_bytes

                                if event == b"control" and payload == b"done":
                                    topic = message.topic.decode()
                                    run_id = topic.split("run:")[1].split(":")[0]
                                    meta_event = b"metadata"
                                    meta_payload = orjson.dumps(
                                        {"status": "run_done", "run_id": run_id}
                                    )
                                    if not should_filter_event(
                                        "metadata", meta_payload
                                    ):
                                        yield (meta_event, meta_payload, message.id)
                                else:
                                    if not should_filter_event(event_name, payload):
                                        yield (event, payload, message.id)

                            except TimeoutError:
                                continue
                            except (ValueError, KeyError):
                                continue

                        # Yield execution to other tasks to prevent event loop starvation
                        await asyncio.sleep(0)

            except WrappedHTTPException as e:
                raise e.http_exception from None
            except asyncio.CancelledError:
                await logger.awarning(
                    "Thread stream client disconnected",
                    thread_id=str(thread_id),
                )
                raise
            except:
                raise
            finally:
                # Clean up all created queues
                for run_id, queue in created_queues:
                    try:
                        await stream_manager.remove_queue(run_id, thread_id, queue)
                    except Exception:
                        # Ignore cleanup errors
                        pass

        @staticmethod
        async def publish(
            thread_id: UUID | str,
            event: str,
            message: bytes,
        ) -> None:
            """Publish a thread-level event to the thread stream."""
            from langgraph_api.utils.stream_codec import STREAM_CODEC

            topic = f"thread:{thread_id}:stream".encode()

            stream_manager = get_stream_manager()
            payload = STREAM_CODEC.encode(event, message)
            await stream_manager.put_thread(
                str(thread_id), Message(topic=topic, data=payload)
            )

        @staticmethod
        async def check_thread_stream_auth(
            thread_id: UUID,
            ctx: Auth.types.BaseAuthContext | None = None,
        ) -> None:
            async with connect() as conn:
                filters = await Threads.Stream.handle_event(
                    ctx,
                    "read",
                    Auth.types.ThreadsRead(thread_id=thread_id),
                )
                if filters:
                    thread = await Threads._get_with_filters(
                        cast(FirestoreConnectionProto, conn), thread_id, filters
                    )
                    if not thread:
                        raise HTTPException(status_code=404, detail="Thread not found")

    @staticmethod
    async def count(
        conn: FirestoreConnectionProto,
        *,
        metadata: MetadataInput = None,
        values: MetadataInput = None,
        status: ThreadStatus | None = None,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> int:
        """Get count of threads for a user."""
        metadata = metadata if metadata is not None else {}
        values = values if values is not None else {}

        username = metadata.get("username")
        if not username:
            raise HTTPException(status_code=400, detail="Metadata username is required")

        threads = conn.store["threads"].get(username, [])
        filters = await Threads.handle_event(
            ctx,
            "search",
            Auth.types.ThreadsSearch(
                metadata=metadata,
                values=values,
                status=status,
                limit=0,
                offset=0,
            ),
        )

        count = 0
        for thread in threads:
            if filters and not _check_filter_match(thread["metadata"], filters):
                continue

            if metadata and not is_jsonb_contained(thread["metadata"], metadata):
                continue

            if (
                values
                and "values" in thread
                and not is_jsonb_contained(thread["values"], values)
            ):
                continue

            if status and thread.get("status") != status:
                continue

            count += 1

        return count


RUN_LOCK = asyncio.Lock()


class Runs(Authenticated):
    resource = "threads"

    @staticmethod
    async def stats(conn: FirestoreConnectionProto) -> QueueStats:
        """Get stats about the queue."""
        pending_runs = [run for run in conn.store["runs"] if run["status"] == "pending"]
        running_runs = [run for run in conn.store["runs"] if run["status"] == "running"]

        if not pending_runs and not running_runs:
            return {
                "n_pending": 0,
                "pending_runs_wait_time_max_secs": None,
                "pending_runs_wait_time_med_secs": None,
                "n_running": 0,
            }

        now = datetime.now(UTC)
        pending_waits: list[float] = []
        for run in pending_runs:
            created_at = run.get("created_at")
            if not isinstance(created_at, datetime):
                continue
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=UTC)
            pending_waits.append((now - created_at).total_seconds())

        max_pending_wait = max(pending_waits) if pending_waits else None
        if pending_waits:
            sorted_waits = sorted(pending_waits)
            half = len(sorted_waits) // 2
            if len(sorted_waits) % 2 == 1:
                med_pending_wait = sorted_waits[half]
            else:
                med_pending_wait = (sorted_waits[half - 1] + sorted_waits[half]) / 2
        else:
            med_pending_wait = None

        return {
            "n_pending": len(pending_runs),
            "n_running": len(running_runs),
            "pending_runs_wait_time_max_secs": max_pending_wait,
            "pending_runs_wait_time_med_secs": med_pending_wait,
        }

    @staticmethod
    async def next(wait: bool, limit: int = 1) -> AsyncIterator[tuple[Run, int]]:
        """Get the next run from the queue, and the attempt number.
        1 is the first attempt, 2 is the first retry, etc."""
        now = datetime.now(UTC)

        if wait:
            await asyncio.sleep(0.5)
        else:
            await asyncio.sleep(0)

        async with connect() as conn, RUN_LOCK:
            pending_runs = sorted(
                [
                    run
                    for run in conn.store["runs"]
                    if run["status"] == "pending" and run.get("created_at", now) < now
                ],
                key=lambda x: x.get("created_at", datetime.min),
            )

            if not pending_runs:
                return

            # Try to lock and get the first available run
            for _, run in zip(range(limit), pending_runs, strict=False):
                if run["status"] != "pending":
                    continue

                run_id = run["run_id"]
                thread_id = run["thread_id"]

                thread = None
                for user_threads in conn.store["threads"].values():
                    thread = next(
                        (t for t in user_threads if t["thread_id"] == thread_id),
                        None,
                    )
                    if thread:
                        break

                if thread is None:
                    await logger.awarning(
                        "Unexpected missing thread in Runs.next",
                        thread_id=run["thread_id"],
                    )
                    continue

                if run["status"] != "pending":
                    continue

                if any(
                    run["status"] == "running"
                    for run in conn.store["runs"]
                    if run["thread_id"] == thread_id
                ):
                    continue
                # Increment attempt counter
                attempt = await conn.retry_counter.increment(run_id)
                # Set run as "running"
                run["status"] = "running"
                yield run, attempt

    @asynccontextmanager
    @staticmethod
    async def enter(
        run_id: UUID,
        thread_id: UUID | None,
        loop: asyncio.AbstractEventLoop,
        resumable: bool,
    ) -> AsyncIterator[ValueEvent]:
        """Enter a run, listen for cancellation while running, signal when done."
        This method should be called as a context manager by a worker executing a run.
        """
        from langgraph_api.asyncio import SimpleTaskGroup, ValueEvent
        from langgraph_api.utils.stream_codec import STREAM_CODEC

        stream_manager = get_stream_manager()
        # Get control queue for this run (normal queue is created during run creation)
        control_queue = await stream_manager.add_control_queue(run_id, thread_id)

        async with SimpleTaskGroup(cancel=True, taskgroup_name="Runs.enter") as tg:
            done = ValueEvent()
            tg.create_task(
                listen_for_cancellation(control_queue, run_id, thread_id, done)
            )

            # Give done event to caller
            yield done
            # Store the control message for late subscribers
            control_message = Message(
                topic=f"run:{run_id}:control".encode(), data=b"done"
            )
            await stream_manager.put(run_id, thread_id, control_message)

            # Signal done to all subscribers using stream codec
            stream_message = Message(
                topic=f"run:{run_id}:stream".encode(),
                data=STREAM_CODEC.encode("control", b"done"),
            )
            await stream_manager.put(
                run_id, thread_id, stream_message, resumable=resumable
            )

            # Remove the control_queue (normal queue is cleaned up during run deletion)
            await stream_manager.remove_control_queue(run_id, thread_id, control_queue)

    @staticmethod
    async def sweep() -> None:
        """Sweep runs that are no longer running"""
        pass

    @staticmethod
    def _merge_jsonb(*objects: dict) -> dict:
        """Mimics PostgreSQL's JSONB merge behavior"""
        result = {}
        for obj in objects:
            if obj is not None:
                result.update(copy.deepcopy(obj))
        return result

    @staticmethod
    def _get_configurable(config: dict) -> dict:
        """Extract configurable from config, mimicking PostgreSQL's coalesce"""
        return config.get("configurable", {})

    @staticmethod
    async def put(
        conn: FirestoreConnectionProto | AsyncConnectionProto,
        assistant_id: UUID,
        kwargs: dict,
        *,
        thread_id: UUID | None = None,
        user_id: str | None = None,
        run_id: UUID | None = None,
        status: RunStatus | None = "pending",
        metadata: MetadataInput,
        prevent_insert_if_inflight: bool,
        multitask_strategy: MultitaskStrategy = "reject",
        if_not_exists: IfNotExists = "reject",
        after_seconds: int = 0,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[Run]:
        """Create a run."""
        from langgraph_api.schema import Run, Thread

        username = _get_username_from_ctx()

        if not isinstance(kwargs, dict):
            raise HTTPException(status_code=400, detail="kwargs must be a dictionary")

        assistant_id = _ensure_uuid(assistant_id)
        assistant = next(
            (a for a in conn.store["assistants"] if a["assistant_id"] == assistant_id),
            None,
        )

        if not assistant:
            return _empty_generator()

        thread_id = _ensure_uuid(thread_id) if thread_id else None
        run_id = _ensure_uuid(run_id) if run_id else None
        config = kwargs.get("config", {})
        temporary = kwargs.get("temporary", False)

        existing_thread = next(
            (
                t
                for t in conn.store["threads"].get(username, [])
                if t["thread_id"] == thread_id
            ),
            None,
        )
        filters = await Runs.handle_event(
            ctx,
            "create_run",
            Auth.types.RunsCreate(
                thread_id=None if temporary else thread_id,
                assistant_id=assistant_id,
                run_id=run_id,
                status=status,
                metadata=metadata,
                prevent_insert_if_inflight=prevent_insert_if_inflight,
                multitask_strategy=multitask_strategy,
                if_not_exists=if_not_exists,
                after_seconds=after_seconds,
                kwargs=kwargs,
            ),
        )
        if existing_thread and filters:
            # Reject if the user doesn't own the thread
            if not _check_filter_match(existing_thread["metadata"], filters):
                return _empty_generator()

        if not existing_thread and (thread_id is None or if_not_exists == "create"):
            # Create new thread
            if thread_id is None:
                thread_id = uuid4()

            thread = Thread(
                thread_id=thread_id,
                status="busy",
                metadata={
                    "graph_id": assistant["graph_id"],
                    "assistant_id": str(assistant_id),
                    **(config.get("metadata") or {}),
                    **metadata,
                },
                config=Runs._merge_jsonb(
                    assistant["config"],
                    config,
                    {
                        "configurable": Runs._merge_jsonb(
                            Runs._get_configurable(assistant["config"]),
                        )
                    },
                ),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                values=b"",
            )

            await logger.ainfo("Creating thread", thread_id=thread_id)
            conn.store["threads"].setdefault(username, []).append(thread)
            await asyncio.to_thread(
                conn.db.collection("users")
                .document(username)
                .collection("threads")
                .document(str(thread_id))
                .set,
                serialize_for_firestore(thread),
            )
        elif existing_thread:
            # Update existing thread
            if existing_thread["status"] != "busy":
                existing_thread["status"] = "busy"
                existing_thread["metadata"] = Runs._merge_jsonb(
                    existing_thread["metadata"],
                    {
                        "graph_id": assistant["graph_id"],
                        "assistant_id": str(assistant_id),
                    },
                )
                existing_thread["config"] = Runs._merge_jsonb(
                    assistant["config"],
                    existing_thread["config"],
                    config,
                    {
                        "configurable": Runs._merge_jsonb(
                            Runs._get_configurable(assistant["config"]),
                            Runs._get_configurable(existing_thread["config"]),
                        )
                    },
                )
                existing_thread["updated_at"] = datetime.now(UTC)
                await asyncio.to_thread(
                    conn.db.collection("users")
                    .document(username)
                    .collection("threads")
                    .document(str(existing_thread["thread_id"]))
                    .update,
                    {
                        "status": existing_thread["status"],
                        "metadata": serialize_for_firestore(
                            existing_thread["metadata"]
                        ),
                        "config": serialize_for_firestore(existing_thread["config"]),
                        "updated_at": existing_thread["updated_at"],
                    },
                )
        else:
            return _empty_generator()

        # Check for inflight runs if needed
        inflight_runs = [
            r
            for r in conn.store["runs"]
            if r["thread_id"] == thread_id and r["status"] in ("pending", "running")
        ]
        if prevent_insert_if_inflight:
            if inflight_runs:

                async def _return_inflight():
                    for run in inflight_runs:
                        yield run

                return _return_inflight()

        # Create new run
        configurable = Runs._merge_jsonb(
            Runs._get_configurable(assistant["config"]),
            (
                Runs._get_configurable(existing_thread["config"])
                if existing_thread
                else {}
            ),
            Runs._get_configurable(config),
            {
                "run_id": str(run_id),
                "thread_id": str(thread_id),
                "graph_id": assistant["graph_id"],
                "assistant_id": str(assistant_id),
                "user_id": (
                    config.get("configurable", {}).get("user_id")
                    or (
                        existing_thread["config"].get("configurable", {}).get("user_id")
                        if existing_thread
                        else None
                    )
                    or assistant["config"].get("configurable", {}).get("user_id")
                    or user_id
                ),
            },
        )
        merged_metadata = Runs._merge_jsonb(
            assistant["metadata"],
            existing_thread["metadata"] if existing_thread else {},
            config.get("metadata") or {},
            metadata,
        )
        new_run = Run(
            run_id=run_id,
            thread_id=thread_id,
            assistant_id=assistant_id,
            metadata=merged_metadata,
            status=status,
            kwargs=Runs._merge_jsonb(
                kwargs,
                {
                    "config": Runs._merge_jsonb(
                        assistant["config"],
                        config,
                        {"configurable": configurable},
                        {
                            "metadata": merged_metadata,
                        },
                    ),
                    "context": Runs._merge_jsonb(
                        assistant.get("context", {}), kwargs.get("context", {})
                    ),
                },
            ),
            multitask_strategy=multitask_strategy,
            created_at=datetime.now(UTC) + timedelta(seconds=after_seconds),
            updated_at=datetime.now(UTC),
        )
        conn.store["runs"].append(new_run)

        async def _yield_new():
            yield new_run
            for r in inflight_runs:
                yield r

        return _yield_new()

    @staticmethod
    async def get(
        conn: FirestoreConnectionProto,
        run_id: UUID,
        *,
        thread_id: UUID,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[Run]:
        """Get a run by ID."""

        run_id, thread_id = _ensure_uuid(run_id), _ensure_uuid(thread_id)
        filters = await Runs.handle_event(
            ctx,
            "read",
            Auth.types.ThreadsRead(thread_id=thread_id),
        )

        async def _yield_result():
            matching_run = None
            for run in conn.store["runs"]:
                if run["run_id"] == run_id and run["thread_id"] == thread_id:
                    matching_run = run
                    break
            if matching_run:
                if filters:
                    thread = await Threads._get_with_filters(
                        conn, matching_run["thread_id"], filters
                    )
                    if not thread:
                        return
                yield matching_run

        return _yield_result()

    @staticmethod
    async def delete(
        conn: FirestoreConnectionProto,
        run_id: UUID,
        *,
        thread_id: UUID,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[UUID]:
        """Delete a run by ID."""
        run_id, thread_id = _ensure_uuid(run_id), _ensure_uuid(thread_id)
        filters = await Runs.handle_event(
            ctx,
            "delete",
            Auth.types.ThreadsDelete(run_id=run_id, thread_id=thread_id),
        )

        if filters:
            thread = await Threads._get_with_filters(conn, thread_id, filters)
            if not thread:
                return _empty_generator()
        _delete_checkpoints_for_thread(thread_id, conn, run_id=run_id)

        found = False
        for i, run in enumerate(conn.store["runs"]):
            if run["run_id"] == run_id and run["thread_id"] == thread_id:
                del conn.store["runs"][i]
                found = True
                break
        if not found:
            raise HTTPException(status_code=404, detail="Run not found")

        async def _yield_deleted():
            await logger.ainfo("Run deleted", run_id=run_id)
            yield run_id

        return _yield_deleted()

    @staticmethod
    async def cancel(
        conn: FirestoreConnectionProto | AsyncConnectionProto,
        run_ids: Sequence[UUID | str] | None = None,
        *,
        action: Literal["interrupt", "rollback"] = "interrupt",
        thread_id: UUID | None = None,
        status: Literal["pending", "running", "all"] | None = None,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> None:
        """
        Cancel runs in memory. Must provide either:
        1) thread_id + run_ids, or
        2) status in {"pending", "running", "all"}.

        Steps:
        - Validate arguments (one usage pattern or the other).
        - Auth check: 'update' event via handle_event().
        - Gather runs matching either the (thread_id, run_ids) set or the given status.
        - For each run found:
            * Send a cancellation message through the stream manager.
            * If 'pending', set to 'interrupted' or delete (if action='rollback' and not actively queued).
            * If 'running', the worker will pick up the message.
            * Otherwise, log a warning for non-cancelable states.
        - 404 if no runs are found or authorized.
        """
        # 1. Validate arguments
        if status is not None:
            # If status is set, user must NOT specify thread_id or run_ids
            if thread_id is not None or run_ids is not None:
                raise HTTPException(
                    status_code=422,
                    detail="Cannot specify 'thread_id' or 'run_ids' when using 'status'",
                )
        else:
            # If status is not set, user must specify both thread_id and run_ids
            if thread_id is None or run_ids is None:
                raise HTTPException(
                    status_code=422,
                    detail="Must provide either a status or both 'thread_id' and 'run_ids'",
                )

        # Convert and normalize inputs
        if run_ids is not None:
            run_ids = [_ensure_uuid(rid) for rid in run_ids]
        if thread_id is not None:
            thread_id = _ensure_uuid(thread_id)

        filters = await Runs.handle_event(
            ctx,
            "update",
            Auth.types.ThreadsUpdate(
                thread_id=thread_id,  # type: ignore
                action=action,
                metadata={
                    "run_ids": run_ids,
                    "status": status,
                },
            ),
        )

        status_list: tuple[str, ...] = ()
        if status is not None:
            if status == "all":
                status_list = ("pending", "running")
            elif status in ("pending", "running"):
                status_list = (status,)
            else:
                raise ValueError(f"Unsupported status: {status}")

        def is_run_match(r: dict) -> bool:
            """
            Check whether a run in `conn.store["runs"]` meets the selection criteria.
            """
            if status_list:
                return r["status"] in status_list
            else:
                return r["thread_id"] == thread_id and r["run_id"] in run_ids  # type: ignore

        candidate_runs = [r for r in conn.store["runs"] if is_run_match(r)]

        if filters:
            # If a run is found but not authorized by the thread filters, skip it
            thread = (
                await Threads._get_with_filters(conn, thread_id, filters)
                if thread_id
                else None
            )
            # If there's no matching thread, no runs are authorized.
            if thread_id and not thread:
                candidate_runs = []
            # Otherwise, we might trust that `_get_with_filters` is the only constraint
            # on thread. If your filters also apply to runs, you might do more checks here.

        if not candidate_runs:
            raise HTTPException(status_code=404, detail="No runs found to cancel.")

        stream_manager = get_stream_manager()
        coros = []
        cancelable_runs = []

        for run in candidate_runs:
            run_id = run["run_id"]
            control_message = Message(
                topic=f"run:{run_id}:control".encode(),
                data=action.encode(),
            )
            coros.append(stream_manager.put(run_id, thread_id, control_message))

            queues = stream_manager.get_queues(run_id, thread_id)

            if run["status"] in ("pending", "running"):
                cancelable_runs.append(run)
                if queues or action != "rollback":
                    if run["status"] == "pending":
                        thread = next(
                            (
                                t
                                for t in conn.store["threads"]
                                if t["thread_id"] == run["thread_id"]
                            ),
                            None,
                        )
                        if thread:
                            thread["status"] = "idle"
                            thread["updated_at"] = datetime.now(tz=UTC)
                    run["status"] = "interrupted"
                    run["updated_at"] = datetime.now(tz=UTC)
                else:
                    await logger.ainfo(
                        "Eagerly deleting pending run with rollback action",
                        run_id=str(run_id),
                        status=run["status"],
                    )
                    coros.append(Runs.delete(conn, run_id, thread_id=run["thread_id"]))
            else:
                await logger.awarning(
                    "Attempted to cancel non-pending run.",
                    run_id=str(run_id),
                    status=run["status"],
                )

        if not cancelable_runs:
            raise HTTPException(
                status_code=404,
                detail="No matching runs to cancel. Please verify the thread ID and run IDs are correct, and the runs haven't been deleted or completed.",
            )

        if coros:
            await asyncio.gather(*coros)

        await logger.ainfo(
            "Cancelled runs",
            run_ids=[str(r["run_id"]) for r in cancelable_runs],
            thread_id=str(thread_id) if thread_id else None,
            status=status,
            action=action,
        )

    @staticmethod
    async def search(
        conn: FirestoreConnectionProto,
        thread_id: UUID,
        *,
        limit: int = 10,
        offset: int = 0,
        status: RunStatus | None = None,
        select: list[RunSelectField] | None = None,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> AsyncIterator[Run]:
        """List all runs by thread."""
        runs = conn.store["runs"]
        metadata = {}
        thread_id = _ensure_uuid(thread_id)
        filters = await Runs.handle_event(
            ctx,
            "search",
            Auth.types.ThreadsSearch(thread_id=thread_id, metadata=metadata),
        )
        filtered_runs = [
            run
            for run in runs
            if run["thread_id"] == thread_id
            and is_jsonb_contained(run["metadata"], metadata)
            and (
                not filters
                or (await Threads._get_with_filters(conn, thread_id, filters))
            )
            and (status is None or run["status"] == status)
        ]
        sorted_runs = sorted(filtered_runs, key=lambda x: x["created_at"], reverse=True)
        sliced_runs = sorted_runs[offset : offset + limit]

        async def _return():
            for run in sliced_runs:
                if select:
                    # Filter to only selected fields
                    filtered_run = {k: v for k, v in run.items() if k in select}
                    yield filtered_run
                else:
                    yield run

        return _return()

    @staticmethod
    async def set_status(
        conn: FirestoreConnectionProto, run_id: UUID, status: RunStatus
    ) -> None:
        """Set the status of a run."""
        # Find the run in the store
        run_id = _ensure_uuid(run_id)
        run = next((run for run in conn.store["runs"] if run["run_id"] == run_id), None)

        if run:
            # Update the status and updated_at timestamp
            run["status"] = status
            run["updated_at"] = datetime.now(tz=UTC)
            return run
        return None

    class Stream:
        @staticmethod
        async def subscribe(
            run_id: UUID,
            thread_id: UUID | None = None,
        ) -> ContextQueue:
            """Subscribe to the run stream, returning a queue."""
            stream_manager = get_stream_manager()
            queue = await stream_manager.add_queue(_ensure_uuid(run_id), thread_id)

            # If there's a control message already stored, send it to the new subscriber
            if thread_id is None:
                thread_id = THREADLESS_KEY
            if control_queues := stream_manager.control_queues.get(thread_id, {}).get(
                run_id
            ):
                for control_queue in control_queues:
                    try:
                        while True:
                            control_msg = control_queue.get()
                            await queue.put(control_msg)
                    except asyncio.QueueEmpty:
                        pass
            return queue

        @staticmethod
        async def join(
            run_id: UUID,
            *,
            stream_channel: asyncio.Queue,
            thread_id: UUID,
            ignore_404: bool = False,
            cancel_on_disconnect: bool = False,
            stream_mode: list[StreamMode] | StreamMode | None = None,
            last_event_id: str | None = None,
            ctx: Auth.types.BaseAuthContext | None = None,
        ) -> AsyncIterator[tuple[bytes, bytes, bytes | None]]:
            """Stream the run output."""
            from langgraph_api.asyncio import create_task
            from langgraph_api.serde import json_dumpb
            from langgraph_api.utils.stream_codec import decode_stream_message

            queue = stream_channel
            try:
                async with connect() as conn:
                    try:
                        await Runs.Stream.check_run_stream_auth(run_id, thread_id, ctx)
                    except HTTPException as e:
                        raise WrappedHTTPException(e) from None
                    run = await Runs.get(conn, run_id, thread_id=thread_id, ctx=ctx)

                    for message in get_stream_manager().restore_messages(
                        run_id, thread_id, last_event_id
                    ):
                        data, id = message.data, message.id
                        decoded = decode_stream_message(data, channel=message.topic)
                        mode = decoded.event_bytes.decode("utf-8")
                        payload = decoded.message_bytes

                        if mode == "control":
                            if payload == b"done":
                                return
                        elif (
                            not stream_mode
                            or mode in stream_mode
                            or (
                                (
                                    "messages" in stream_mode
                                    or "messages-tuple" in stream_mode
                                )
                                and mode.startswith("messages")
                            )
                        ):
                            yield mode.encode(), payload, id
                            logger.debug(
                                "Replayed run event",
                                run_id=str(run_id),
                                message_id=id,
                                stream_mode=mode,
                                data=data,
                            )

                    while True:
                        try:
                            # Wait for messages with a timeout
                            message = await asyncio.wait_for(queue.get(), timeout=0.5)
                            data, id = message.data, message.id
                            decoded = decode_stream_message(data, channel=message.topic)
                            mode = decoded.event_bytes.decode("utf-8")
                            payload = decoded.message_bytes

                            if mode == "control":
                                if payload == b"done":
                                    break
                            elif (
                                not stream_mode
                                or mode in stream_mode
                                or (
                                    (
                                        "messages" in stream_mode
                                        or "messages-tuple" in stream_mode
                                    )
                                    and mode.startswith("messages")
                                )
                            ):
                                yield mode.encode(), payload, id
                                logger.debug(
                                    "Streamed run event",
                                    run_id=str(run_id),
                                    stream_mode=mode,
                                    message_id=id,
                                    data=payload,
                                )
                        except TimeoutError:
                            # Check if the run is still pending
                            run_iter = await Runs.get(
                                conn, run_id, thread_id=thread_id, ctx=ctx
                            )
                            run = await anext(run_iter, None)

                            if ignore_404 and run is None:
                                break
                            elif run is None:
                                yield (
                                    b"error",
                                    json_dumpb(
                                        HTTPException(
                                            status_code=404, detail="Run not found"
                                        )
                                    ),
                                    None,
                                )
                                break
                            elif run["status"] not in ("pending", "running"):
                                break
            except WrappedHTTPException as e:
                raise e.http_exception from None
            except:
                if cancel_on_disconnect:
                    create_task(cancel_run(thread_id, run_id))
                raise
            finally:
                stream_manager = get_stream_manager()
                await stream_manager.remove_queue(run_id, thread_id, queue)

        @staticmethod
        async def check_run_stream_auth(
            run_id: UUID,
            thread_id: UUID,
            ctx: Auth.types.BaseAuthContext | None = None,
        ) -> None:
            async with connect() as conn:
                filters = await Runs.handle_event(
                    ctx,
                    "read",
                    Auth.types.ThreadsRead(thread_id=thread_id),
                )
                if filters:
                    thread = await Threads._get_with_filters(
                        cast(FirestoreConnectionProto, conn), thread_id, filters
                    )
                    if not thread:
                        raise HTTPException(status_code=404, detail="Thread not found")

        @staticmethod
        async def publish(
            run_id: UUID | str,
            event: str,
            message: bytes,
            *,
            thread_id: UUID | str | None = None,
            resumable: bool = False,
        ) -> None:
            """Publish a message to all subscribers of the run stream."""
            from langgraph_api.utils.stream_codec import STREAM_CODEC

            topic = f"run:{run_id}:stream".encode()

            stream_manager = get_stream_manager()
            # Send to all queues subscribed to this run_id using protocol frame
            payload = STREAM_CODEC.encode(event, message)
            await stream_manager.put(
                run_id, thread_id, Message(topic=topic, data=payload), resumable
            )


async def listen_for_cancellation(
    queue: asyncio.Queue, run_id: UUID, thread_id: UUID | None, done: ValueEvent
):
    """Listen for cancellation messages and set the done event accordingly."""
    from langgraph_api.errors import UserInterrupt, UserRollback

    stream_manager = get_stream_manager()

    if control_key := stream_manager.get_control_key(run_id, thread_id):
        payload = control_key.data
        if payload == b"rollback":
            done.set(UserRollback())
        elif payload == b"interrupt":
            done.set(UserInterrupt())

    while not done.is_set():
        try:
            # This task gets cancelled when Runs.enter exits anyway,
            # so we can have a pretty lengthy timeout here
            message = await asyncio.wait_for(queue.get(), timeout=240)
            payload = message.data
            if payload == b"rollback":
                done.set(UserRollback())
            elif payload == b"interrupt":
                done.set(UserInterrupt())
            elif payload == b"done":
                done.set()
                break
        except TimeoutError:
            break


def _delete_checkpoints_for_thread(
    thread_id: str | UUID,
    conn: FirestoreConnectionProto,
    run_id: str | UUID | None = None,
):
    checkpointer = Checkpointer()
    thread_id = str(thread_id)
    if thread_id not in checkpointer.storage:
        return
    if run_id:
        # Look through metadata
        run_id = str(run_id)
        for checkpoint_ns, checkpoints in list(checkpointer.storage[thread_id].items()):
            for checkpoint_id, (_, metadata_b, _) in list(checkpoints.items()):
                metadata = checkpointer.serde.loads_typed(metadata_b)
                if metadata.get("run_id") == run_id:
                    del checkpointer.storage[thread_id][checkpoint_ns][checkpoint_id]
                    if not checkpointer.storage[thread_id][checkpoint_ns]:
                        del checkpointer.storage[thread_id][checkpoint_ns]
    else:
        del checkpointer.storage[thread_id]
        # Keys are (thread_id, checkpoint_ns, checkpoint_id)
        checkpointer.writes = defaultdict()


class Checkpoints(Authenticated):
    """Firestore-based Checkpoints operations."""

    resource = "threads"

    @staticmethod
    @retry_db
    async def put(
        conn: FirestoreConnectionProto,
        thread_id: str | UUID,
        checkpoint_id: str | None = None,
        checkpoint: dict | None = None,
        metadata: dict | None = None,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> None:
        """Store a checkpoint.

        Args:
            conn: Firestore connection
            thread_id: Thread ID
            checkpoint_id: Checkpoint ID
            checkpoint: Checkpoint data
            metadata: Checkpoint metadata
            ctx: Auth context
        """
        thread_id = str(_ensure_uuid(thread_id))

        # Store checkpoint in subcollection
        checkpoint_data = {
            "checkpoint_id": checkpoint_id or str(uuid4()),
            "thread_id": thread_id,
            "checkpoint": checkpoint or {},
            "metadata": metadata or {},
            "created_at": datetime.now(UTC),
        }

        checkpoint_ref = (
            conn.db.collection("threads")
            .document(thread_id)
            .collection("checkpoints")
            .document(checkpoint_data["checkpoint_id"])
        )

        await asyncio.to_thread(checkpoint_ref.set, checkpoint_data, merge=True)

    @staticmethod
    @retry_db
    async def get(
        conn: FirestoreConnectionProto,
        thread_id: str | UUID,
        checkpoint_id: str | None = None,
        ctx: Auth.types.BaseAuthContext | None = None,
    ) -> dict | None:
        """Get a checkpoint.

        Args:
            conn: Firestore connection
            thread_id: Thread ID
            checkpoint_id: Checkpoint ID (latest if not specified)
            ctx: Auth context

        Returns:
            Checkpoint data or None
        """
        thread_id = str(_ensure_uuid(thread_id))

        if checkpoint_id:
            checkpoint_ref = (
                conn.db.collection("threads")
                .document(thread_id)
                .collection("checkpoints")
                .document(checkpoint_id)
            )
            doc = await asyncio.to_thread(checkpoint_ref.get)
            if doc.exists:
                return doc.to_dict().get("checkpoint")
        else:
            # Get latest checkpoint
            query = (
                conn.db.collection("threads")
                .document(thread_id)
                .collection("checkpoints")
                .order_by("created_at", direction="DESCENDING")
                .limit(1)
            )
            docs = await asyncio.to_thread(lambda: list(query.stream()))
            if docs:
                return docs[0].to_dict().get("checkpoint")

        return None


class _ContextQueue(asyncio.Queue):
    """Queue that supports async context manager protocol."""

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        # Clear the queue
        while not self.empty():
            try:
                self.get_nowait()
            except asyncio.QueueEmpty:
                break


class Crons(Authenticated):
    """Firestore-based Crons operations."""

    resource = "crons"

    # TODO: Implement Crons operations
    pass


async def cancel_run(
    thread_id: UUID, run_id: UUID, ctx: Auth.types.BaseAuthContext | None = None
) -> None:
    async with connect() as conn:
        await Runs.cancel(conn, [run_id], thread_id=thread_id, ctx=ctx)


class StreamHandler:
    """Handles SSE streaming for real-time updates."""

    def __init__(self):
        self._subscribers: dict[str, set] = defaultdict(set)

    async def stream(
        self,
        thread_id: str,
        *,
        last_event_id: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream events for a thread.

        Args:
            thread_id: Thread to stream from
            last_event_id: Resume from this event ID

        Yields:
            SSE formatted event strings
        """
        # TODO: Implement Firestore streaming
        # For now, yield a keep-alive ping
        while True:
            await asyncio.sleep(30)
            yield ": ping\n\n"

    async def send_event(
        self,
        thread_id: str,
        event: str,
        data: dict[str, Any],
    ) -> None:
        """Send event to all subscribers.

        Args:
            thread_id: Thread ID
            event: Event type (e.g., "run_start", "stream")
            data: Event data
        """
        # TODO: Implement event publishing to Firestore
        pass


def _check_filter_match(metadata: dict, filters: Auth.types.FilterType | None) -> bool:
    """Check if metadata matches the filter conditions.

    Args:
        metadata: The metadata to check
        filters: The filter conditions to apply

    Returns:
        True if the metadata matches all filter conditions, False otherwise
    """
    if not filters:
        return True

    for key, value in filters.items():
        if isinstance(value, dict):
            op = next(iter(value))
            filter_value = value[op]

            if op == "$eq":
                if key not in metadata or metadata[key] != filter_value:
                    return False
            elif op == "$contains":
                if key not in metadata or not isinstance(metadata[key], list):
                    return False

                if isinstance(filter_value, list):
                    # Mimick Postgres containment operator behavior.
                    # It would be more efficient to use set operations here,
                    # but we can't assume that elements are hashable.
                    # The Postgres algorithm is also O(n^2).
                    for filter_element in filter_value:
                        if filter_element not in metadata[key]:
                            return False
                elif filter_value not in metadata[key]:
                    return False
        else:
            # Direct equality
            if key not in metadata or metadata[key] != value:
                return False

    return True


async def _empty_generator():
    if False:
        yield


def _check_filter_match(metadata: dict, filters: Auth.types.FilterType | None) -> bool:
    """Check if metadata matches the filter conditions.

    Args:
        metadata: The metadata to check
        filters: The filter conditions to apply

    Returns:
        True if the metadata matches all filter conditions, False otherwise
    """
    if not filters:
        return True

    for key, value in filters.items():
        if isinstance(value, dict):
            op = next(iter(value))
            filter_value = value[op]

            if op == "$eq":
                if key not in metadata or metadata[key] != filter_value:
                    return False
            elif op == "$contains":
                if key not in metadata or not isinstance(metadata[key], list):
                    return False

                if isinstance(filter_value, list):
                    # Mimick Postgres containment operator behavior.
                    # It would be more efficient to use set operations here,
                    # but we can't assume that elements are hashable.
                    # The Postgres algorithm is also O(n^2).
                    for filter_element in filter_value:
                        if filter_element not in metadata[key]:
                            return False
                elif filter_value not in metadata[key]:
                    return False
        else:
            # Direct equality
            if key not in metadata or metadata[key] != value:
                return False

    return True


# Update __all__ to include StreamHandler
__all__ = ["Assistants", "Threads", "Runs", "Crons", "StreamHandler"]
