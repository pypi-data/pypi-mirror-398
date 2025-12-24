import asyncio
import os
import uuid
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any, NotRequired
from uuid import UUID

import structlog
from firebase_admin import credentials, firestore, initialize_app
from google.cloud import firestore as gcf_firestore
from langgraph.checkpoint.memory import PersistentDict
from typing_extensions import TypedDict

from langgraph_runtime_firestore.serialize import (
    deserialize_from_firestore,
)

if TYPE_CHECKING:
    from langgraph_api.utils import AsyncConnectionProto

logger = structlog.stdlib.get_logger(__name__)


class Assistant(TypedDict):
    assistant_id: UUID
    graph_id: str
    name: str
    description: str | None
    created_at: NotRequired[datetime]
    updated_at: NotRequired[datetime]
    config: dict[str, Any]
    context: dict[str, Any]
    metadata: dict[str, Any]


class Thread(TypedDict):
    thread_id: UUID
    created_at: NotRequired[datetime]
    updated_at: NotRequired[datetime]
    metadata: dict[str, Any]
    status: str


class Run(TypedDict):
    run_id: UUID
    thread_id: UUID
    assistant_id: UUID
    created_at: NotRequired[datetime]
    updated_at: NotRequired[datetime]
    metadata: dict[str, Any]
    status: str


class RunEvent(TypedDict):
    event_id: UUID
    run_id: UUID
    received_at: NotRequired[datetime]
    span_id: UUID
    event: str
    name: str
    tags: list[Any]
    data: dict[str, Any]
    metadata: dict[str, Any]


class AssistantVersion(TypedDict):
    assistant_id: UUID
    version: int
    graph_id: str
    config: dict[str, Any]
    context: dict[str, Any]
    metadata: dict[str, Any]
    created_at: NotRequired[datetime]
    name: str


class GlobalStore(dict):
    """In-memory dict-like store backed by Firestore collections."""

    def __init__(self, db: gcf_firestore.Client | None = None):
        super().__init__()
        self.db = db
        self._initialize_empty()

    def _initialize_empty(self):
        """Initialize empty store structure."""
        self["runs"] = []
        self["threads"] = {}
        self["assistants"] = []
        self["assistant_versions"] = []

    async def load_from_firestore(self):
        """Load store data from Firestore collections."""
        if not self.db:
            logger.warning("Firestore client not available, using empty store")
            return

        try:
            self["assistants"] = [
                deserialize_from_firestore(doc.to_dict())
                for doc in self.db.collection("assistants").get()
            ]

            for user_doc in self.db.collection("users").get():
                username = user_doc.id
                self["threads"][username] = [
                    deserialize_from_firestore(doc.to_dict())
                    for doc in user_doc.reference.collection("threads").get()
                ]

            logger.info(
                "Store loaded from Firestore",
                assistants=len(self["assistants"]),
                threads=len(self["threads"]),
            )
        except Exception as e:
            logger.error("Failed to load store from Firestore", exc_info=e)
            raise

    def clear(self):
        """Clear the store, keeping only system-created assistants."""
        assistants = self.get("assistants", [])
        super().clear()
        self._initialize_empty()
        # Keep system-created assistants
        self["assistants"] = [
            a for a in assistants if a.get("metadata", {}).get("created_by") == "system"
        ]


OPS_FILENAME = os.path.join(".langgraph_api", ".langgraph_ops.pckl")
RETRY_COUNTER_FILENAME = os.path.join(".langgraph_api", ".langgraph_retry_counter.pckl")


class InMemoryRetryCounter:
    def __init__(self):
        self._counters: dict[uuid.UUID, int] = PersistentDict(
            int, filename=RETRY_COUNTER_FILENAME
        )
        self._locks: dict[uuid.UUID, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def increment(self, run_id: uuid.UUID) -> int:
        async with self._locks[run_id]:
            self._counters[run_id] += 1
            return self._counters[run_id]

    def close(self):
        self._counters.close()


# Global retry counter for in-memory implementation
GLOBAL_RETRY_COUNTER = InMemoryRetryCounter()
GLOBAL_STORE = GlobalStore()


class FirestoreConnectionProto:
    """Firestore connection wrapper for async operations."""

    def __init__(self, db: gcf_firestore.Client):
        self.db = db
        self.filename = OPS_FILENAME
        self.store = GLOBAL_STORE
        self.retry_counter = GLOBAL_RETRY_COUNTER
        self.can_execute = False

    @asynccontextmanager
    async def pipeline(self):
        yield None

    async def execute(self, query: str, *args, **kwargs):
        return None

    def clear(self):
        self.store.clear()
        keys = list(self.retry_counter._counters)
        for key in keys:
            del self.retry_counter._counters[key]
        keys = list(self.retry_counter._locks)
        for key in keys:
            del self.retry_counter._locks[key]
        if os.path.exists(self.filename):
            os.remove(self.filename)


app = None
db = None


def initialize_firestore_cached() -> gcf_firestore.Client:
    """Initialize Firebase Admin SDK and Firestore."""

    # ✓ Validate required environment variables
    credentials_path = os.getenv("FIRESTORE_CREDENTIALS_PATH")
    project_id = os.getenv("FIRESTORE_PROJECT_ID")

    if not credentials_path or not project_id:
        raise ValueError(
            "FIRESTORE_CREDENTIALS_PATH and FIRESTORE_PROJECT_ID must be set"
        )

    # ✓ Initialize Firebase
    global app, db
    if db is not None:
        return db
    try:
        app = initialize_app(
            credentials.Certificate(credentials_path), {"projectId": project_id}
        )
        db = firestore.client()

        logger.info("Firestore initialized", project_id=project_id)
        return db

    except FileNotFoundError as e:
        logger.error("Credentials file not found", credentials_path=credentials_path)
        raise ValueError(
            f"Invalid FIRESTORE_CREDENTIALS_PATH: {credentials_path}"
        ) from e

    except Exception as e:
        logger.error("Failed to initialize Firestore", exc_info=e)
        raise


@asynccontextmanager
async def connect(
    *, supports_core_api: bool = False, __test__: bool = False
) -> AsyncIterator["AsyncConnectionProto"]:
    """Create an async connection to Firestore."""
    db = initialize_firestore_cached()
    # Set db on GLOBAL_STORE if not already set
    if not GLOBAL_STORE.db:
        GLOBAL_STORE.db = db
    # Load data from Firestore on first connection
    if not GLOBAL_STORE.get("_loaded"):
        await GLOBAL_STORE.load_from_firestore()
        GLOBAL_STORE["_loaded"] = True
    yield FirestoreConnectionProto(db)


async def start_pool() -> None:
    """Initialize Firestore connection pool."""
    try:
        db = initialize_firestore_cached()
        GLOBAL_STORE.db = db
        # Load data from Firestore on pool start
        if not GLOBAL_STORE.get("_loaded"):
            await GLOBAL_STORE.load_from_firestore()
            GLOBAL_STORE["_loaded"] = True
        logger.info("Firestore connection pool started")

    except Exception as e:
        logger.error(f"Failed to start Firestore pool: {e}")
        raise


async def stop_pool() -> None:
    """Clean up Firestore connection pool."""
    try:
        from firebase_admin import delete_app

        delete_app(app)

        logger.info("Firestore connection pool stopped")
    except Exception as e:
        logger.error(f"Failed to stop Firestore pool: {e}")


async def healthcheck() -> None:
    """Health check for Firestore connection."""
    try:
        db = initialize_firestore_cached()
        await asyncio.to_thread(
            db.collection("_healthcheck").document("ping").set,
            {"timestamp": datetime.now()},
        )
    except Exception as e:
        logger.error(f"Firestore health check failed: {e}")
        raise


def pool_stats(*args, **kwargs) -> dict[str, dict[str, int]]:
    """Return Firestore pool statistics."""
    return {
        "firestore": {
            "connections": 1,  # Firestore client manages its own pool
        }
    }
