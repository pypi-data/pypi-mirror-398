from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    AsyncIterator,
    Iterator,
    cast,
    AsyncGenerator,
)
import logging
from datetime import datetime
import os
import asyncio
from dotenv import load_dotenv

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from google.cloud.exceptions import GoogleCloudError
from google.oauth2 import service_account

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    PendingWrite,  # Note: PendingWrite is actually Tuple[str, Any, Any]
    get_checkpoint_id,
    WRITES_IDX_MAP,
    ChannelVersions,
)
from langgraph.checkpoint.serde.base import SerializerProtocol
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.pregel.types import StateSnapshot
from langchain_core.runnables import RunnableConfig

from botrun_flow_lang.constants import CHECKPOINTER_STORE_NAME
from botrun_flow_lang.services.base.firestore_base import FirestoreBase
import time

load_dotenv()

# Set up logger
logger = logging.getLogger("AsyncFirestoreCheckpointer")
# 從環境變數取得日誌級別，默認為 WARNING（不顯示 INFO 級別日誌）
log_level = os.getenv("FIRESTORE_CHECKPOINTER_LOG_LEVEL", "WARNING").upper()
log_level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
logger.setLevel(log_level_map.get(log_level, logging.WARNING))
# Create console handler if it doesn't exist
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(log_level_map.get(log_level, logging.WARNING))
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Constants for field names
FIELD_THREAD_ID = "thread_id"
FIELD_CHECKPOINT_NS = "checkpoint_ns"
FIELD_CHECKPOINT_ID = "checkpoint_id"
FIELD_PARENT_CHECKPOINT_ID = "parent_checkpoint_id"
FIELD_TASK_ID = "task_id"
FIELD_IDX = "idx"
FIELD_TIMESTAMP = "timestamp"
FIELD_TYPE = "type"
FIELD_DATA = "data"
FIELD_METADATA = "metadata"
FIELD_NEW_VERSIONS = "new_versions"
FIELD_CHANNEL = "channel"
FIELD_VALUE = "value"
FIELD_CREATED_AT = "created_at"


class AsyncFirestoreCheckpointer(BaseCheckpointSaver):
    """Async Firestore-based checkpoint saver implementation.

    This implementation uses Firestore's collections and sub-collections to efficiently
    store and retrieve checkpoints and their associated writes.

    For each environment, it creates:
    - A root collection for all checkpoints
    - A sub-collection for each checkpoint's writes

    This design provides:
    - Efficient querying by thread_id, namespace, and checkpoint_id
    - Hierarchical structure that matches the data relationships
    - Improved query performance with proper indexing
    """

    db: firestore.AsyncClient
    checkpoints_collection: firestore.AsyncCollectionReference

    def __init__(
        self,
        env_name: str,
        serializer: Optional[SerializerProtocol] = None,
        collection_name: Optional[str] = None,
    ):
        """Initialize the AsyncFirestoreCheckpointer.

        Args:
            env_name: Environment name to be used as prefix for collection.
            serializer: Optional serializer to use for converting values to storable format.
            collection_name: Optional custom collection name. If not provided,
                             it will use {env_name}-{CHECKPOINTER_STORE_NAME}.
        """
        super().__init__()
        logger.info(f"Initializing AsyncFirestoreCheckpointer with env_name={env_name}")
        self.serde = serializer or JsonPlusSerializer()
        self._collection_name = (
            collection_name or f"{env_name}-{CHECKPOINTER_STORE_NAME}"
        )
        logger.info(f"Using collection: {self._collection_name}")

        try:
            # Initialize async Firestore client
            google_service_account_key_path = os.getenv(
                "GOOGLE_APPLICATION_CREDENTIALS_FOR_FASTAPI",
                "/app/keys/scoop-386004-d22d99a7afd9.json",
            )
            credentials = service_account.Credentials.from_service_account_file(
                google_service_account_key_path,
                scopes=["https://www.googleapis.com/auth/datastore"],
            )

            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if project_id:
                self.db = firestore.AsyncClient(
                    project=project_id, credentials=credentials
                )
            else:
                self.db = firestore.AsyncClient(credentials=credentials)

            self.checkpoints_collection = self.db.collection(self._collection_name)
            logger.info("Async Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Firestore client: {e}", exc_info=True)
            raise

    async def close(self):
        """Close the Firestore client connection."""
        if hasattr(self, "db") and self.db:
            await self.db.close()
            logger.info("Firestore client connection closed")

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        await self.close()

    def _get_checkpoint_doc_id(
        self, thread_id: str, checkpoint_ns: str, checkpoint_id: str
    ) -> str:
        """Generate a document ID for a checkpoint.

        For maximum Firestore efficiency, we use a compound ID that naturally clusters
        related data together for efficient retrieval.
        """
        return f"{thread_id}:{checkpoint_ns}:{checkpoint_id}"

    def _get_writes_subcollection(
        self, checkpoint_doc_ref: firestore.AsyncDocumentReference
    ) -> firestore.AsyncCollectionReference:
        """Get the subcollection reference for checkpoint writes."""
        return checkpoint_doc_ref.collection("writes")

    def _parse_checkpoint_doc_id(self, doc_id: str) -> Dict[str, str]:
        """Parse a checkpoint document ID into its components."""
        parts = doc_id.split(":")
        if len(parts) != 3:
            raise ValueError(f"Invalid checkpoint document ID format: {doc_id}")

        return {
            FIELD_THREAD_ID: parts[0],
            FIELD_CHECKPOINT_NS: parts[1],
            FIELD_CHECKPOINT_ID: parts[2],
        }

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Save a checkpoint to Firestore asynchronously.

        This method saves a checkpoint to Firestore as a document with fields for
        efficient querying.

        Args:
            config: The config to associate with the checkpoint.
            checkpoint: The checkpoint to save.
            metadata: Additional metadata to save with the checkpoint.
            new_versions: New channel versions as of this write.

        Returns:
            RunnableConfig: Updated configuration after storing the checkpoint.
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = checkpoint["id"]
        parent_checkpoint_id = config["configurable"].get("checkpoint_id", "")

        # Generate document ID for efficient querying
        doc_id = self._get_checkpoint_doc_id(thread_id, checkpoint_ns, checkpoint_id)

        # Serialize the data
        type_, serialized_checkpoint = self.serde.dumps_typed(checkpoint)
        serialized_metadata = self.serde.dumps(metadata)

        # Prepare the document data
        data = {
            FIELD_THREAD_ID: thread_id,
            FIELD_CHECKPOINT_NS: checkpoint_ns,
            FIELD_CHECKPOINT_ID: checkpoint_id,
            FIELD_PARENT_CHECKPOINT_ID: parent_checkpoint_id,
            FIELD_TYPE: type_,
            FIELD_DATA: serialized_checkpoint,
            FIELD_METADATA: serialized_metadata,
            FIELD_TIMESTAMP: firestore.SERVER_TIMESTAMP,  # Use server timestamp for consistency
            FIELD_CREATED_AT: datetime.utcnow().isoformat(),  # Backup client-side timestamp
        }

        if new_versions:
            data[FIELD_NEW_VERSIONS] = self.serde.dumps(new_versions)

        try:
            await self.checkpoints_collection.document(doc_id).set(data)
            logger.info(f"Successfully stored checkpoint with ID: {doc_id}")
        except Exception as e:
            logger.error(f"Error storing checkpoint: {e}", exc_info=True)
            raise

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        }

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: List[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Store intermediate writes linked to a checkpoint asynchronously.

        This method saves intermediate writes associated with a checkpoint in a subcollection.

        Args:
            config: Configuration of the related checkpoint.
            writes: List of writes to store, each as (channel, value) pair.
            task_id: Identifier for the task creating the writes.
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"]["checkpoint_id"]

        # Get the checkpoint document reference
        checkpoint_doc_id = self._get_checkpoint_doc_id(
            thread_id, checkpoint_ns, checkpoint_id
        )
        checkpoint_doc_ref = self.checkpoints_collection.document(checkpoint_doc_id)

        # Get the writes subcollection
        writes_collection = self._get_writes_subcollection(checkpoint_doc_ref)

        try:
            # Optimize write operations with batching
            batch = self.db.batch()
            batch_size = 0
            max_batch_size = 450  # Slightly below Firestore limit for safety
            batch_futures = []  # For tracking concurrent batch commits

            for idx, (channel, value) in enumerate(writes):
                # Determine the write ID
                write_idx = WRITES_IDX_MAP.get(channel, idx)
                write_id = f"{task_id}:{write_idx}"

                # Serialize the value
                type_, serialized_value = self.serde.dumps_typed(value)

                # Prepare the write data
                data = {
                    FIELD_TASK_ID: task_id,
                    FIELD_IDX: write_idx,
                    FIELD_CHANNEL: channel,
                    FIELD_TYPE: type_,
                    FIELD_VALUE: serialized_value,
                    FIELD_TIMESTAMP: firestore.SERVER_TIMESTAMP,
                    FIELD_CREATED_AT: datetime.utcnow().isoformat(),
                }

                write_doc_ref = writes_collection.document(write_id)

                # Determine if we should set or create-if-not-exists
                if channel in WRITES_IDX_MAP:
                    # For indexed channels, always set (similar to HSET behavior)
                    batch.set(write_doc_ref, data)
                else:
                    # For non-indexed channels, we need a transaction to check existence
                    # We'll check existence manually for now
                    doc = await write_doc_ref.get()
                    if not doc.exists:
                        batch.set(write_doc_ref, data)

                batch_size += 1

                # If batch is getting full, submit it and start a new one
                if batch_size >= max_batch_size:
                    batch_futures.append(batch.commit())
                    batch = self.db.batch()
                    batch_size = 0

            # Commit any remaining writes in the batch
            if batch_size > 0:
                batch_futures.append(batch.commit())

            # Wait for all batch operations to complete
            if batch_futures:
                await asyncio.gather(*batch_futures)

            logger.info(
                f"Successfully stored {len(writes)} writes for checkpoint: {checkpoint_id}"
            )
        except Exception as e:
            logger.error(f"Error storing writes: {e}", exc_info=True)
            raise

    async def aget_tuple(
        self,
        config: RunnableConfig,
    ) -> Optional[CheckpointTuple]:
        """Get a checkpoint tuple from Firestore asynchronously.

        This method retrieves a checkpoint and its associated writes from Firestore.

        Args:
            config: The config to use for retrieving the checkpoint.

        Returns:
            Optional[CheckpointTuple]: The retrieved checkpoint tuple, or None if not found.
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = get_checkpoint_id(config)
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

        try:
            # If checkpoint_id is provided, get that specific checkpoint
            if checkpoint_id:
                doc_id = self._get_checkpoint_doc_id(
                    thread_id, checkpoint_ns, checkpoint_id
                )
                doc = await self.checkpoints_collection.document(doc_id).get()

                if not doc.exists:
                    return None
            else:
                # Otherwise, find the latest checkpoint
                query = (
                    self.checkpoints_collection.where(
                        filter=FieldFilter(FIELD_THREAD_ID, "==", thread_id)
                    )
                    .where(filter=FieldFilter(FIELD_CHECKPOINT_NS, "==", checkpoint_ns))
                    .order_by(FIELD_TIMESTAMP, direction=firestore.Query.DESCENDING)
                    .limit(1)
                )

                docs = await query.get()
                if not docs:
                    return None

                doc = docs[0]
                # Extract the checkpoint_id for loading writes
                checkpoint_id = doc.get(FIELD_CHECKPOINT_ID)

            data = doc.to_dict()

            # Parse the document data
            type_ = data.get(FIELD_TYPE)
            serialized_checkpoint = data.get(FIELD_DATA)
            serialized_metadata = data.get(FIELD_METADATA)

            if not type_ or not serialized_checkpoint or not serialized_metadata:
                logger.error(f"Invalid checkpoint data for ID: {doc.id}")
                return None

            # 重新組合類型和序列化數據，以符合 loads_typed 的期望
            checkpoint = self.serde.loads_typed((type_, serialized_checkpoint))
            metadata = self.serde.loads(serialized_metadata)

            # Load pending writes from the subcollection
            pending_writes = await self._aload_pending_writes(doc.reference)

            return CheckpointTuple(
                config=config,
                checkpoint=checkpoint,
                metadata=metadata,
                pending_writes=pending_writes if pending_writes else None,
            )
        except Exception as e:
            logger.error(f"Error retrieving checkpoint tuple: {e}", exc_info=True)
            raise

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncGenerator[CheckpointTuple, None]:
        """List checkpoints from Firestore asynchronously.

        This method retrieves a list of checkpoint tuples from Firestore based
        on the provided config.

        Args:
            config: Base configuration for filtering checkpoints.
            filter: Additional filtering criteria for metadata.
            before: If provided, only checkpoints before the specified checkpoint ID are returned.
            limit: Maximum number of checkpoints to return.

        Yields:
            AsyncGenerator[CheckpointTuple, None]: An async generator of matching checkpoint tuples.
        """
        if not config:
            logger.error("Config is required for listing checkpoints")
            return

        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

        try:
            t1 = time.time()
            # Build the query
            query = (
                self.checkpoints_collection.where(
                    filter=FieldFilter(FIELD_THREAD_ID, "==", thread_id)
                )
                .where(filter=FieldFilter(FIELD_CHECKPOINT_NS, "==", checkpoint_ns))
                .order_by(FIELD_TIMESTAMP, direction=firestore.Query.DESCENDING)
            )

            # Apply additional filters
            if before is not None:
                before_id = get_checkpoint_id(before)
                # We need to find the timestamp of the 'before' checkpoint to filter correctly
                before_doc_id = self._get_checkpoint_doc_id(
                    thread_id, checkpoint_ns, before_id
                )
                before_doc = await self.checkpoints_collection.document(
                    before_doc_id
                ).get()

                if before_doc.exists:
                    before_timestamp = before_doc.get(FIELD_TIMESTAMP)
                    if before_timestamp:
                        query = query.where(FIELD_TIMESTAMP, "<", before_timestamp)

            # Apply limit if provided
            if limit is not None:
                query = query.limit(limit)

            # Execute the query
            docs = await query.get()

            # Process each document
            for doc in docs:
                data = doc.to_dict()

                if not data or FIELD_DATA not in data or FIELD_METADATA not in data:
                    continue

                # Extract basic information
                thread_id = data.get(FIELD_THREAD_ID)
                checkpoint_ns = data.get(FIELD_CHECKPOINT_NS)
                checkpoint_id = data.get(FIELD_CHECKPOINT_ID)

                # Build config for this checkpoint
                checkpoint_config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": checkpoint_id,
                    }
                }

                # Parse checkpoint data
                type_ = data.get(FIELD_TYPE)
                serialized_checkpoint = data.get(FIELD_DATA)
                serialized_metadata = data.get(FIELD_METADATA)

                if not type_ or not serialized_checkpoint:
                    continue

                # 重新組合類型和序列化數據，以符合 loads_typed 的期望
                checkpoint = self.serde.loads_typed((type_, serialized_checkpoint))
                metadata = (
                    self.serde.loads(serialized_metadata)
                    if serialized_metadata
                    else None
                )

                # Load pending writes
                pending_writes = await self._aload_pending_writes(doc.reference)

                yield CheckpointTuple(
                    config=checkpoint_config,
                    checkpoint=checkpoint,
                    metadata=metadata,
                    pending_writes=pending_writes if pending_writes else None,
                )
        except Exception as e:
            logger.error(f"Error listing checkpoints: {e}", exc_info=True)
            raise
        t2 = time.time()
        print(f"[AsyncFirestoreCheckpointer:alist] Elapsed {t2 - t1:.3f}s")

    async def _aload_pending_writes(
        self, checkpoint_doc_ref: firestore.AsyncDocumentReference
    ) -> List[Tuple[str, Any, None]]:
        """Load pending writes for a checkpoint from its subcollection.

        Returns a flat list of PendingWrite tuples (channel, value, None) similar to Redis implementation.
        """
        try:
            # Get the writes subcollection
            writes_collection = self._get_writes_subcollection(checkpoint_doc_ref)

            # Query all writes documents in the subcollection
            docs = await writes_collection.get()

            # Process the documents to extract writes
            result = []

            for doc in docs:
                data = doc.to_dict()

                if not data:
                    continue

                task_id = data.get(FIELD_TASK_ID)
                channel = data.get(FIELD_CHANNEL)
                type_ = data.get(FIELD_TYPE)
                serialized_value = data.get(FIELD_VALUE)

                if not task_id or not channel or not type_ or not serialized_value:
                    continue

                # 重新組合類型和序列化數據，以符合 loads_typed 的期望
                value = self.serde.loads_typed((type_, serialized_value))

                # Create a proper tuple according to PendingWrite definition (channel, value, None)
                # Following the Redis implementation pattern
                result.append((channel, value, None))

            return result
        except Exception as e:
            logger.error(f"Error loading pending writes: {e}", exc_info=True)
            return []

    async def adelete_thread(self, thread_id: str) -> None:
        """Delete all checkpoints and writes for a specific thread asynchronously.

        This method removes all data associated with a thread, including:
        - All checkpoint documents that match the thread_id
        - All writes subcollections under those checkpoints

        Args:
            thread_id: The thread ID for which to delete all checkpoints and writes.
        """
        try:
            logger.info(f"Starting deletion of all data for thread: {thread_id}")

            # Query all checkpoint documents for this thread_id
            # We need to delete across all checkpoint namespaces
            query = self.checkpoints_collection.where(
                filter=FieldFilter(FIELD_THREAD_ID, "==", thread_id)
            )

            # Get all matching checkpoint documents
            docs = await query.get()

            if not docs:
                logger.info(f"No checkpoints found for thread: {thread_id}")
                return

            deleted_checkpoints = 0
            deleted_writes = 0
            total_operations = 0
            batch_count = 0

            # Use smaller batches to avoid "Transaction too big" error
            batch = self.db.batch()
            batch_size = 0
            max_batch_size = 200  # Conservative batch size

            async def commit_current_batch():
                """Commit the current batch if it has operations"""
                nonlocal batch, batch_size, total_operations, batch_count
                if batch_size > 0:
                    await batch.commit()
                    total_operations += batch_size
                    batch_count += 1
                    logger.info(
                        f"Thread {thread_id}: Committed batch {batch_count} "
                        f"({batch_size} operations, total: {total_operations})"
                    )
                    batch = self.db.batch()
                    batch_size = 0

            for doc in docs:
                # Delete writes subcollection first
                writes_collection = self._get_writes_subcollection(doc.reference)

                # Get all writes documents in the subcollection
                writes_docs = await writes_collection.get()

                # Add writes deletion to batch
                for write_doc in writes_docs:
                    batch.delete(write_doc.reference)
                    batch_size += 1
                    deleted_writes += 1

                    # Commit batch when it reaches max size
                    if batch_size >= max_batch_size:
                        await commit_current_batch()

                # Add checkpoint document deletion to batch
                batch.delete(doc.reference)
                batch_size += 1
                deleted_checkpoints += 1

                # Commit batch when it reaches max size
                if batch_size >= max_batch_size:
                    await commit_current_batch()

            # Commit any remaining operations in the final batch
            await commit_current_batch()

            logger.info(
                f"Successfully deleted thread {thread_id}: "
                f"{deleted_checkpoints} checkpoints, {deleted_writes} writes "
                f"(total: {total_operations} operations in {batch_count} batches)"
            )

        except Exception as e:
            logger.error(f"Error deleting thread {thread_id}: {e}", exc_info=True)
            raise
