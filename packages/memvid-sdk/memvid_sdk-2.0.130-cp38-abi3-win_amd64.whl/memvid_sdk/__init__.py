"""Python SDK entry point exposing the unified ``use`` factory."""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Union
from typing import Literal

from . import _lib

# Base error class - all SDK errors inherit from this
MemvidError = _lib.MemvidError

# MV001: Storage capacity exceeded
CapacityExceededError = _lib.CapacityExceededError

# MV002: Invalid ticket signature
TicketInvalidError = _lib.TicketInvalidError

# MV003: Ticket sequence replay attack
TicketReplayError = _lib.TicketReplayError

# MV004: Lexical index not enabled
LexIndexDisabledError = _lib.LexIndexDisabledError

# MV005: Time index missing or invalid
TimeIndexMissingError = _lib.TimeIndexMissingError

# MV006: File verification failed
VerifyFailedError = _lib.VerifyFailedError

# MV007: File locked by another process
_LockedError = getattr(_lib, "LockedError", None)
if _LockedError is None:
    class LockedError(MemvidError):  # type: ignore[misc]
        """File is locked by another process (MV007)."""
        pass
else:
    LockedError = _LockedError

# MV008: API key required for this operation
_ApiKeyRequiredError = getattr(_lib, "ApiKeyRequiredError", None)
if _ApiKeyRequiredError is None:
    class ApiKeyRequiredError(MemvidError):  # type: ignore[misc]
        """API key required for this operation (MV008)."""
        pass
else:
    ApiKeyRequiredError = _ApiKeyRequiredError

# MV009: Memory already bound to another file
_MemoryAlreadyBoundError = getattr(_lib, "MemoryAlreadyBoundError", None)
if _MemoryAlreadyBoundError is None:
    class MemoryAlreadyBoundError(MemvidError):  # type: ignore[misc]
        """Memory already bound to another file (MV009)."""
        pass
else:
    MemoryAlreadyBoundError = _MemoryAlreadyBoundError

# MV010: Frame not found
_FrameNotFoundError = getattr(_lib, "FrameNotFoundError", None)
if _FrameNotFoundError is None:
    class FrameNotFoundError(MemvidError):  # type: ignore[misc]
        """Requested frame does not exist (MV010)."""
        pass
else:
    FrameNotFoundError = _FrameNotFoundError

# MV011: Vector index not enabled
_VecIndexDisabledError = getattr(_lib, "VecIndexDisabledError", None)
if _VecIndexDisabledError is None:
    class VecIndexDisabledError(MemvidError):  # type: ignore[misc]
        """Vector index not enabled (MV011)."""
        pass
else:
    VecIndexDisabledError = _VecIndexDisabledError

# MV012: Corrupt file detected
_CorruptFileError = getattr(_lib, "CorruptFileError", None)
if _CorruptFileError is None:
    class CorruptFileError(MemvidError):  # type: ignore[misc]
        """File corruption detected (MV012)."""
        pass
else:
    CorruptFileError = _CorruptFileError

# MV013: File not found
_FileNotFoundError = getattr(_lib, "FileNotFoundError", None)
if _FileNotFoundError is None:
    class FileNotFoundError(MemvidError):  # type: ignore[misc]
        """File not found (MV013)."""
        pass
else:
    FileNotFoundError = _FileNotFoundError

# MV014: Vector dimension mismatch
_VecDimensionMismatchError = getattr(_lib, "VecDimensionMismatchError", None)
if _VecDimensionMismatchError is None:
    class VecDimensionMismatchError(MemvidError):  # type: ignore[misc]
        """Vector dimension mismatch (MV014)."""
        pass
else:
    VecDimensionMismatchError = _VecDimensionMismatchError

# MV015: Embedding failed
_EmbeddingFailedError = getattr(_lib, "EmbeddingFailedError", None)
if _EmbeddingFailedError is None:
    class EmbeddingFailedError(MemvidError):  # type: ignore[misc]
        """Embedding failed (MV015)."""
        pass
else:
    EmbeddingFailedError = _EmbeddingFailedError

# MV016: Encryption/decryption error (.mv2e)
_EncryptionError = getattr(_lib, "EncryptionError", None)
if _EncryptionError is None:
    class EncryptionError(MemvidError):  # type: ignore[misc]
        """Encryption/decryption error (.mv2e) (MV016)."""
        pass
else:
    EncryptionError = _EncryptionError

# MV017: NER model not available
_NerModelNotAvailableError = getattr(_lib, "NerModelNotAvailableError", None)
if _NerModelNotAvailableError is None:
    class NerModelNotAvailableError(MemvidError):  # type: ignore[misc]
        """NER model not available (MV017)."""
        pass
else:
    NerModelNotAvailableError = _NerModelNotAvailableError

# MV018: CLIP index not enabled
_ClipIndexDisabledError = getattr(_lib, "ClipIndexDisabledError", None)
if _ClipIndexDisabledError is None:
    class ClipIndexDisabledError(MemvidError):  # type: ignore[misc]
        """CLIP index not enabled (MV018)."""
        pass
else:
    ClipIndexDisabledError = _ClipIndexDisabledError

_MemvidCore = _lib._MemvidCore
_open = _lib.open
_put = _lib.put
_find = _lib.find
_ask = _lib.ask
_verify = getattr(_lib, "verify", None)
_lock_who = getattr(_lib, "lock_who", None)
_lock_nudge = getattr(_lib, "lock_nudge", None)
_lock_capsule = getattr(_lib, "lock", None)
_unlock_capsule = getattr(_lib, "unlock", None)
_version_info = getattr(_lib, "version_info", None)
from ._registry import registry
from ._sentinel import NoOp
from ._analytics import track_command, flush as flush_analytics, is_telemetry_enabled

# Ensure adapter modules register their loaders.
from . import adapters as _adapters  # noqa: F401

# Import embeddings module
from . import embeddings

# Import CLIP and entities modules
from . import clip
from . import entities

# Stable kind identifiers shared across bindings.
Kind = Literal[
    "basic",
    "langchain",
    "llamaindex",
    "crewai",
    "vercel-ai",
    "openai",
    "autogen",
    "haystack",
    "langgraph",
    "semantic-kernel",
    "mcp",
]

ApiKey = Union[str, Mapping[str, str]]

_MEMVID_EMBEDDING_PROVIDER_KEY = "memvid.embedding.provider"
_MEMVID_EMBEDDING_MODEL_KEY = "memvid.embedding.model"
_MEMVID_EMBEDDING_DIMENSION_KEY = "memvid.embedding.dimension"
_MEMVID_EMBEDDING_NORMALIZED_KEY = "memvid.embedding.normalized"


def _normalise_apikey(apikey: Optional[ApiKey]) -> Optional[Dict[str, str]]:
    if apikey is None:
        return None
    if isinstance(apikey, str):
        return {"default": apikey}
    return {str(key): str(value) for key, value in apikey.items()}


def _apply_embedding_identity_metadata(
    metadata: MutableMapping[str, Any],
    identity: Mapping[str, Any],
    embedding_dimension: Optional[int],
) -> None:
    provider_raw = identity.get("provider")
    model_raw = identity.get("model")
    dimension_raw = identity.get("dimension", embedding_dimension)
    normalized_raw = identity.get("normalized")

    provider = str(provider_raw).strip().lower() if provider_raw is not None else None
    model = str(model_raw).strip() if model_raw is not None else None

    if not provider and not model:
        return

    if provider:
        metadata[_MEMVID_EMBEDDING_PROVIDER_KEY] = provider
    if model:
        metadata[_MEMVID_EMBEDDING_MODEL_KEY] = model

    if dimension_raw is not None:
        try:
            dimension = int(dimension_raw)
        except (TypeError, ValueError):
            dimension = None
        if dimension and dimension > 0:
            metadata[_MEMVID_EMBEDDING_DIMENSION_KEY] = dimension

    if normalized_raw is not None:
        metadata[_MEMVID_EMBEDDING_NORMALIZED_KEY] = bool(normalized_raw)


def _embedding_identity_from_embedder(embedder: "embeddings.EmbeddingProvider") -> Dict[str, Any]:
    provider = embedder.__class__.__name__.lower()
    if isinstance(embedder, embeddings.OpenAIEmbeddings):
        provider = "openai"
    elif isinstance(embedder, embeddings.CohereEmbeddings):
        provider = "cohere"
    elif isinstance(embedder, embeddings.VoyageEmbeddings):
        provider = "voyage"
    elif hasattr(embeddings, "NvidiaEmbeddings") and isinstance(embedder, embeddings.NvidiaEmbeddings):
        provider = "nvidia"
    elif isinstance(embedder, embeddings.HuggingFaceEmbeddings):
        provider = "huggingface"
    elif hasattr(embeddings, "HashEmbeddings") and isinstance(embedder, getattr(embeddings, "HashEmbeddings")):
        provider = "custom"

    return {
        "provider": provider,
        "model": getattr(embedder, "model_name", None),
        "dimension": getattr(embedder, "dimension", None),
        "normalized": None,
    }


class Memvid:
    """High-level facade over the compiled memvid-core handle.

    Supports context manager protocol for automatic resource cleanup:

    Example:
        >>> with memvid_sdk.use("basic", "data.mv2") as mem:
        ...     mem.put("Title", "label", {}, text="content")
        ...     results = mem.find("query")
        ... # File handle automatically closed

    Or for more control:
        >>> mem = memvid_sdk.use("basic", "data.mv2")
        >>> try:
        ...     mem.put("Title", "label", {}, text="content")
        ... finally:
        ...     mem.close()
    """

    def __init__(
        self,
        *,
        kind: str,
        core: _MemvidCore,
        attachments: Mapping[str, Any],
    ):
        self._kind = kind
        self._core = core
        self._closed = False
        self.tools = attachments.get(
            "tools", NoOp(f"kind '{kind}' did not register tools", f"memvid.{kind}.tools")
        )
        self.functions = attachments.get("functions", [])
        self.nodes = attachments.get(
            "nodes", NoOp(f"kind '{kind}' did not register nodes", f"memvid.{kind}.nodes")
        )
        self.as_query_engine = attachments.get("as_query_engine")

    def __enter__(self) -> "Memvid":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager, closing the handle."""
        self.close()
        return None  # Don't suppress exceptions

    @property
    def path(self) -> str:
        return self._core.path()

    def put(
        self,
        title: Optional[str] = None,
        label: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        *,
        text: Optional[str] = None,
        file: Optional[str] = None,
        uri: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
        labels: Optional[Sequence[str]] = None,
        kind: Optional[str] = None,
        track: Optional[str] = None,
        search_text: Optional[str] = None,
        enable_embedding: bool = False,
        embedding_model: Optional[str] = None,
        auto_tag: bool = True,
        extract_dates: bool = True,
        vector_compression: bool = False,
    ) -> str:
        # Set vector compression mode if requested
        if vector_compression:
            self._core.set_vector_compression(True)

        # Default title from filename if file provided
        if title is None:
            if file:
                title = Path(file).stem
            else:
                title = "Untitled"

        # Default label from file extension or "text"
        if label is None:
            if file:
                label = Path(file).suffix.lstrip(".") or "file"
            else:
                label = "text"

        payload: MutableMapping[str, Any] = {
            "title": title,
            "label": label,
            "metadata": dict(metadata) if metadata else {},
            "enable_embedding": enable_embedding,
            "auto_tag": auto_tag,
            "extract_dates": extract_dates,
        }
        if text is not None:
            payload["text"] = text
        if file is not None:
            payload["file"] = file
        if uri is not None:
            payload["uri"] = uri
        if tags is not None:
            payload["tags"] = list(tags)
        merged_labels = list(labels or [])
        if label not in merged_labels:
            merged_labels.insert(0, label)
        payload["labels"] = merged_labels
        if kind is not None:
            payload["kind"] = kind
        if track is not None:
            payload["track"] = track
        if search_text is not None:
            payload["search_text"] = search_text
        if embedding_model is not None:
            payload["embedding_model"] = embedding_model
        frame_id = self._core.put(payload)
        track_command(self.path, "put", True)
        return str(frame_id)

    def put_many(
        self,
        requests: Sequence[Mapping[str, Any]],
        *,
        embeddings: Optional[Sequence[Sequence[float]]] = None,
        embedder: Optional["embeddings.EmbeddingProvider"] = None,
        embedding_identity: Optional[Mapping[str, Any]] = None,
        opts: Optional[Mapping[str, Any]] = None,
    ) -> List[str]:
        """
        Batch ingestion of multiple documents in a single operation.

        Eliminates Python FFI overhead by processing all documents in Rust,
        providing 100x+ speedup compared to individual put() calls.

        Args:
            requests: List of document dictionaries, each containing:
                - title (str, required): Document title
                - label (str, required): Primary label/category
                - text (str, required): Document content
                - uri (str, optional): Document URI
                - metadata (dict, optional): Key-value metadata
                - tags (list[str], optional): List of tags
                - labels (list[str], optional): Additional labels

            opts: Optional dict with batch operation settings:
                - compression_level (int): 0=none, 1=fast, 3=default, 11=max (default: 3)
                - disable_auto_checkpoint (bool): Skip auto-checkpoint during batch (default: True)
                - skip_sync (bool): Skip fsync for maximum speed (default: False)
                - enable_embedding (bool): Generate embeddings (default: False)
                - auto_tag (bool): Auto-extract tags (default: False)
                - extract_dates (bool): Extract dates from content (default: False)

        Returns:
            List of frame IDs as strings

        Example:
            >>> docs = [
            ...     {"title": "Doc 1", "label": "news", "text": "First document..."},
            ...     {"title": "Doc 2", "label": "news", "text": "Second document..."},
            ... ]
            >>> frame_ids = mem.put_many(docs)
            >>> print(f"Ingested {len(frame_ids)} documents")
        """
        if not requests:
            return []

        if embedder is not None and embeddings is not None:
            raise ValueError("Pass either embeddings=... or embedder=..., not both")

        if embedder is not None and embeddings is None:
            texts = [str(req.get("text", "")) for req in requests]
            embeddings = embedder.embed_documents(texts)
            if embedding_identity is None:
                embedding_identity = _embedding_identity_from_embedder(embedder)

        # Validate each request has required fields
        for i, req in enumerate(requests):
            if not isinstance(req, Mapping):
                raise ValueError(f"Request {i} must be a dict, got {type(req)}")
            if "title" not in req:
                raise ValueError(f"Request {i} missing required field 'title'")
            if "label" not in req:
                raise ValueError(f"Request {i} missing required field 'label'")
            if "text" not in req:
                raise ValueError(f"Request {i} missing required field 'text'")

        # Convert requests to list of dicts (ensure mutable for FFI)
        validated_requests = []
        for req in requests:
            doc = {
                "title": req["title"],
                "label": req["label"],
                "text": req["text"],
            }
            if "uri" in req and req["uri"] is not None:
                doc["uri"] = req["uri"]
            if "metadata" in req:
                doc["metadata"] = dict(req["metadata"])
            else:
                doc["metadata"] = {}
            if "tags" in req:
                doc["tags"] = list(req["tags"])
            else:
                doc["tags"] = []
            if "labels" in req:
                doc["labels"] = list(req["labels"])
            else:
                doc["labels"] = []
            validated_requests.append(doc)

        embedding_dimension: Optional[int] = None
        if embeddings is not None:
            if len(embeddings) != len(validated_requests):
                raise ValueError(
                    f"Embeddings length ({len(embeddings)}) must match requests length ({len(validated_requests)})"
                )
            if embeddings:
                embedding_dimension = len(embeddings[0])
                for i, vec in enumerate(embeddings):
                    if len(vec) != embedding_dimension:
                        raise ValueError(
                            f"Embeddings must have consistent dimension (expected {embedding_dimension}, got {len(vec)} at index {i})"
                        )

        if embedding_identity is not None and embeddings is not None:
            for doc in validated_requests:
                meta = doc.get("metadata")
                if not isinstance(meta, dict):
                    meta = {}
                    doc["metadata"] = meta
                _apply_embedding_identity_metadata(meta, embedding_identity, embedding_dimension)

        # Prepare options dict for FFI
        opts_dict = {}
        if opts:
            if "compression_level" in opts:
                opts_dict["compression_level"] = opts["compression_level"]
            if "disable_auto_checkpoint" in opts:
                opts_dict["disable_auto_checkpoint"] = opts["disable_auto_checkpoint"]
            if "skip_sync" in opts:
                opts_dict["skip_sync"] = opts["skip_sync"]
            if "enable_embedding" in opts:
                opts_dict["enable_embedding"] = opts["enable_embedding"]
            if "embedding_model" in opts:
                opts_dict["embedding_model"] = opts["embedding_model"]
            if "auto_tag" in opts:
                opts_dict["auto_tag"] = opts["auto_tag"]
            if "extract_dates" in opts:
                opts_dict["extract_dates"] = opts["extract_dates"]

        # Call FFI binding (GIL will be released in Rust)
        frame_ids = self._core.put_many(validated_requests, embeddings, opts_dict if opts_dict else None)

        # Convert to strings
        return [str(fid) for fid in frame_ids]

    def find(
        self,
        query: str,
        *,
        k: int = 5,
        snippet_chars: int = 240,
        scope: Optional[str] = None,
        cursor: Optional[str] = None,
        mode: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        query_embedding_model: Optional[str] = None,
        adaptive: Optional[bool] = None,
        min_relevancy: Optional[float] = None,
        max_k: Optional[int] = None,
        adaptive_strategy: Optional[str] = None,
        embedder: Optional["embeddings.EmbeddingProvider"] = None,
        as_of_frame: Optional[int] = None,
        as_of_ts: Optional[int] = None,
    ) -> Dict[str, Any]:
        if embedder is not None and query_embedding is not None:
            raise ValueError("Pass either query_embedding=... or embedder=..., not both")
        if embedder is not None and query_embedding is None and (mode or "auto") != "lex":
            query_embedding = embedder.embed_query(query)

        result = self._core.find(
            query,
            k=k,
            snippet_chars=snippet_chars,
            scope=scope,
            cursor=cursor,
            mode=mode,
            query_embedding=query_embedding,
            query_embedding_model=query_embedding_model,
            adaptive=adaptive,
            min_relevancy=min_relevancy,
            max_k=max_k,
            adaptive_strategy=adaptive_strategy,
            as_of_frame=as_of_frame,
            as_of_ts=as_of_ts,
        )
        track_command(self.path, "find", True)
        return result

    def ask(
        self,
        question: str,
        *,
        k: int = 6,
        mode: str = "auto",
        snippet_chars: int = 320,
        scope: Optional[str] = None,
        since: Optional[int] = None,
        until: Optional[int] = None,
        context_only: bool = False,
        query_embedding: Optional[List[float]] = None,
        query_embedding_model: Optional[str] = None,
        adaptive: Optional[bool] = None,
        min_relevancy: Optional[float] = None,
        max_k: Optional[int] = None,
        adaptive_strategy: Optional[str] = None,
        embedder: Optional["embeddings.EmbeddingProvider"] = None,
        model: Optional[str] = None,
        llm_context_chars: Optional[int] = None,
        api_key: Optional[str] = None,
        mask_pii: bool = False,
    ) -> Dict[str, Any]:
        if embedder is not None and query_embedding is not None:
            raise ValueError("Pass either query_embedding=... or embedder=..., not both")
        if embedder is not None and query_embedding is None and mode != "lex":
            query_embedding = embedder.embed_query(question)

        response = self._core.ask(
            question,
            k=k,
            mode=mode,
            snippet_chars=snippet_chars,
            scope=scope,
            since=since,
            until=until,
            context_only=context_only,
            query_embedding=query_embedding,
            query_embedding_model=query_embedding_model,
            adaptive=adaptive,
            min_relevancy=min_relevancy,
            max_k=max_k,
            adaptive_strategy=adaptive_strategy,
            model=model,
            llm_context_chars=llm_context_chars,
            api_key=api_key,
        )

        # Apply PII masking if requested
        if mask_pii:
            from ._lib import mask_pii as _mask_pii_fn

            # Mask the aggregated context
            if "context" in response:
                response["context"] = _mask_pii_fn(response["context"])

            # Mask the answer
            if "answer" in response and response["answer"]:
                response["answer"] = _mask_pii_fn(response["answer"])

            # Mask answer_lines
            if "answer_lines" in response and response["answer_lines"]:
                response["answer_lines"] = [_mask_pii_fn(line) for line in response["answer_lines"]]

            # Mask text in each hit
            if "hits" in response:
                for hit in response["hits"]:
                    if "text" in hit:
                        hit["text"] = _mask_pii_fn(hit["text"])
                    if "chunk_text" in hit and hit["chunk_text"]:
                        hit["chunk_text"] = _mask_pii_fn(hit["chunk_text"])
                    if "snippet" in hit and hit["snippet"]:
                        hit["snippet"] = _mask_pii_fn(hit["snippet"])
                    if "tags" in hit and hit["tags"]:
                        hit["tags"] = [_mask_pii_fn(tag) for tag in hit["tags"]]
                    if "labels" in hit and hit["labels"]:
                        hit["labels"] = [_mask_pii_fn(label) for label in hit["labels"]]

            # Mask context_fragments
            if "context_fragments" in response:
                for fragment in response["context_fragments"]:
                    if "text" in fragment and fragment["text"]:
                        fragment["text"] = _mask_pii_fn(fragment["text"])

            # Mask sources
            if "sources" in response:
                for source in response["sources"]:
                    if "snippet" in source and source["snippet"]:
                        source["snippet"] = _mask_pii_fn(source["snippet"])
                    if "tags" in source and source["tags"]:
                        source["tags"] = [_mask_pii_fn(tag) for tag in source["tags"]]
                    if "labels" in source and source["labels"]:
                        source["labels"] = [_mask_pii_fn(label) for label in source["labels"]]

            # Mask primary_source
            if "primary_source" in response and response["primary_source"]:
                ps = response["primary_source"]
                if "snippet" in ps and ps["snippet"]:
                    ps["snippet"] = _mask_pii_fn(ps["snippet"])
                if "tags" in ps and ps["tags"]:
                    ps["tags"] = [_mask_pii_fn(tag) for tag in ps["tags"]]
                if "labels" in ps and ps["labels"]:
                    ps["labels"] = [_mask_pii_fn(label) for label in ps["labels"]]

        return response

    def timeline(
        self,
        *,
        limit: int = 100,
        since: Optional[int] = None,
        until: Optional[int] = None,
        reverse: bool = False,
        as_of_frame: Optional[int] = None,
        as_of_ts: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query the timeline with optional Replay filters.

        Args:
            limit: Maximum number of entries to return
            since: Filter entries with timestamp >= since (Unix timestamp)
            until: Filter entries with timestamp <= until (Unix timestamp)
            reverse: Return entries in reverse chronological order
            as_of_frame: Replay filter - only show frames with ID <= as_of_frame
            as_of_ts: Replay filter - only show frames with timestamp <= as_of_ts

        Returns:
            List of timeline entries
        """
        return self._core.timeline(
            limit=limit,
            since=since,
            until=until,
            reverse=reverse,
            as_of_frame=as_of_frame,
            as_of_ts=as_of_ts,
        )

    def stats(self) -> Dict[str, Any]:
        result = self._core.stats()
        track_command(self.path, "stats", True)
        return result

    def seal(self) -> None:
        self._core.seal()

    def commit(self) -> None:
        """Explicitly commit pending WAL/index changes."""
        self._core.commit()

    def commit_parallel(self, opts=None) -> None:
        """Commit using parallel build if available (no-op fallback if not compiled)."""
        from memvid_sdk._lib import BuildOpts
        commit_parallel = getattr(self._core, "commit_parallel", None)
        if commit_parallel is not None:
            if opts is None:
                opts = BuildOpts()
            commit_parallel(opts)
        else:
            self.commit()

    def frame(self, uri: str) -> Dict[str, Any]:
        return self._core.frame(uri)

    def blob(self, uri: str) -> bytes:
        return self._core.blob(uri)

    def close(self) -> None:
        """Close the file handle and release resources.

        Safe to call multiple times. After closing, most operations
        will raise RuntimeError.
        """
        if self._closed:
            return
        try:
            self._core.close()
        except RuntimeError:
            pass
        finally:
            self._closed = True

    @property
    def closed(self) -> bool:
        """True if the handle has been closed."""
        return self._closed

    def enable_lex(self) -> None:
        self._core.enable_lex()

    def enable_vec(self) -> None:
        self._core.enable_vec()

    def apply_ticket(self, ticket: str) -> None:
        self._core.apply_ticket(ticket)

    def get_memory_binding(self) -> Optional[Dict[str, Any]]:
        """Get the current memory binding, if any."""
        return self._core.get_memory_binding()

    def unbind_memory(self) -> None:
        """Unbind from the dashboard memory."""
        self._core.unbind_memory()

    def get_capacity(self) -> int:
        """Get the current capacity in bytes."""
        return self._core.get_capacity()

    def current_ticket(self) -> Dict[str, Any]:
        """Get the current ticket information."""
        return self._core.current_ticket()

    def sync_tickets(
        self,
        memory_id: str,
        api_key: str,
        api_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sync tickets from the API and apply to this file."""
        return self._core.sync_tickets(memory_id, api_key, api_url)

    def verify(self, path: Optional[str] = None, *, deep: bool = False) -> Dict[str, Any]:
        if _verify is None:
            raise RuntimeError("verify support not available in this build")
        if isinstance(self, Memvid):
            resolved = self.path if path is None else str(path)
        else:
            resolved = str(self)
        return _verify(resolved, deep=deep)

    def doctor(
        self,
        path: Optional[str] = None,
        *,
        rebuild_time_index: bool = False,
        rebuild_lex_index: bool = False,
        rebuild_vec_index: bool = False,
        vacuum: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        from ._lib import doctor as _doctor

        if isinstance(self, Memvid):
            resolved = self.path if path is None else str(path)
        else:
            resolved = str(self)
        return _doctor(
            resolved,
            rebuild_time_index=rebuild_time_index,
            rebuild_lex_index=rebuild_lex_index,
            rebuild_vec_index=rebuild_vec_index,
            vacuum=vacuum,
            dry_run=dry_run,
        )

    def put_pdf_tables(
        self,
        pdf_path: str,
        *,
        embed_rows: bool = True,
    ) -> Dict[str, Any]:
        """Extract tables from a PDF and store them in the memory.

        Args:
            pdf_path: Path to the PDF file
            embed_rows: If True, embed individual rows for semantic search

        Returns:
            Dict with extraction results including table_count and table_ids
        """
        return self._core.put_pdf_tables(pdf_path, embed_rows=embed_rows)

    def list_tables(self) -> List[Dict[str, Any]]:
        """List all tables stored in the memory.

        Returns:
            List of table metadata dicts with table_id, row_count, col_count, etc.
        """
        return self._core.list_tables()

    def get_table(
        self,
        table_id: str,
        *,
        format: str = "dict",
    ) -> Any:
        """Retrieve a table by ID.

        Args:
            table_id: The table identifier
            format: Output format - "dict" (default), "csv", or "json"

        Returns:
            Table data in the requested format
        """
        return self._core.get_table(table_id, format=format)

    # ─────────────────────────────────────────────────────────────────────────
    # Session Recording / Time-Travel Replay
    # ─────────────────────────────────────────────────────────────────────────

    def session_start(self, name: Optional[str] = None) -> str:
        """Start a new recording session.

        All subsequent operations (put, find, ask) will be recorded until
        session_end() is called. Sessions can be replayed later with different
        parameters for debugging or testing.

        Args:
            name: Optional descriptive name for the session

        Returns:
            Session ID (UUID string)

        Example:
            >>> session_id = mem.session_start("Debug Session")
            >>> mem.put("Title", "label", {}, text="content")
            >>> results = mem.find("query")
            >>> session = mem.session_end()
        """
        session_start_fn = getattr(self._core, "session_start", None)
        if session_start_fn is None:
            raise RuntimeError("session_start not available - replay feature not compiled")
        return session_start_fn(name)

    def session_end(self) -> Dict[str, Any]:
        """End the current recording session.

        Returns:
            Session summary dict with:
                - session_id: UUID string
                - name: Session name (if provided)
                - created_secs: Unix timestamp when session started
                - ended_secs: Unix timestamp when session ended
                - action_count: Number of recorded actions
                - checkpoint_count: Number of checkpoints
                - duration_secs: Total session duration
        """
        session_end_fn = getattr(self._core, "session_end", None)
        if session_end_fn is None:
            raise RuntimeError("session_end not available - replay feature not compiled")
        return session_end_fn()

    def session_list(self) -> List[Dict[str, Any]]:
        """List all recorded sessions.

        Returns:
            List of session summary dicts (same format as session_end)
        """
        session_list_fn = getattr(self._core, "session_list", None)
        if session_list_fn is None:
            raise RuntimeError("session_list not available - replay feature not compiled")
        return session_list_fn()

    def session_replay(
        self,
        session_id: str,
        *,
        top_k: Optional[int] = None,
        adaptive: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Replay a recorded session with optional parameter overrides.

        This enables "time-travel debugging" - re-running a session with
        different search parameters to understand how results change.

        Args:
            session_id: UUID of the session to replay
            top_k: Override top-k for search operations
            adaptive: Override adaptive retrieval setting

        Returns:
            Replay result dict with:
                - total_actions: Total actions in session
                - matched_actions: Actions that matched original results
                - mismatched_actions: Actions with different results
                - skipped_actions: Actions that were skipped
                - match_rate: Percentage of matching actions
                - total_duration_ms: Replay duration in milliseconds
                - success: Whether replay completed successfully
                - action_results: Detailed results for each action
        """
        session_replay_fn = getattr(self._core, "session_replay", None)
        if session_replay_fn is None:
            raise RuntimeError("session_replay not available - replay feature not compiled")

        return session_replay_fn(session_id, top_k=top_k, adaptive=adaptive)

    def session_delete(self, session_id: str) -> bool:
        """Delete a recorded session.

        Args:
            session_id: UUID of the session to delete

        Returns:
            True if session was deleted, False if not found
        """
        session_delete_fn = getattr(self._core, "session_delete", None)
        if session_delete_fn is None:
            raise RuntimeError("session_delete not available - replay feature not compiled")
        return session_delete_fn(session_id)

    def session_checkpoint(self) -> Optional[str]:
        """Add a checkpoint to the current recording session.

        Checkpoints mark specific points in the session that can be
        used for partial replay or analysis.

        Returns:
            Checkpoint ID if in a session, None otherwise
        """
        session_checkpoint_fn = getattr(self._core, "session_checkpoint", None)
        if session_checkpoint_fn is None:
            raise RuntimeError("session_checkpoint not available - replay feature not compiled")
        return session_checkpoint_fn()

    # ─────────────────────────────────────────────────────────────────────────
    # Memory Cards & Enrichment
    # ─────────────────────────────────────────────────────────────────────────

    def memories(
        self,
        *,
        entity: Optional[str] = None,
        slot: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get memory cards (SPO triplets) stored in the memory.

        Memory cards represent structured knowledge extracted from frames
        in Subject-Predicate-Object (entity-slot-value) format.

        Args:
            entity: Optional entity name to filter by (e.g., "alice")
            slot: Optional slot/predicate to filter by (e.g., "employer")

        Returns:
            Dict with:
                - cards: List of memory card dicts
                - count: Total number of matching cards

        Example:
            >>> result = mem.memories(entity="alice")
            >>> for card in result["cards"]:
            ...     print(f"{card['entity']} -> {card['slot']}: {card['value']}")
        """
        memories_fn = getattr(self._core, "memories", None)
        if memories_fn is None:
            raise RuntimeError("memories not available - feature not compiled")
        return memories_fn(entity, slot)

    def memories_stats(self) -> Dict[str, Any]:
        """Get memory statistics.

        Returns counts of entities, cards, slots, and other memory-related metrics.

        Returns:
            Dict with:
                - entity_count: Number of unique entities
                - card_count: Total number of memory cards
                - slot_count: Number of unique slot types
                - cards_by_kind: Breakdown by card kind (fact, attribute, etc.)
                - enriched_frames: Number of frames that have been enriched
                - last_enrichment: Timestamp of last enrichment (or None)

        Example:
            >>> stats = mem.memories_stats()
            >>> print(f"Entities: {stats['entity_count']}, Cards: {stats['card_count']}")
        """
        memories_stats_fn = getattr(self._core, "memories_stats", None)
        if memories_stats_fn is None:
            raise RuntimeError("memories_stats not available - feature not compiled")
        return memories_stats_fn()

    def memory_entities(self) -> List[str]:
        """Get all entity names stored in memory.

        Returns:
            List of entity names (lowercase)

        Example:
            >>> entities = mem.memory_entities()
            >>> print(f"Known entities: {entities}")
        """
        memory_entities_fn = getattr(self._core, "memory_entities", None)
        if memory_entities_fn is None:
            raise RuntimeError("memory_entities not available - feature not compiled")
        return memory_entities_fn()

    def state(
        self,
        entity: str,
        *,
        slot: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get the current state of an entity (O(1) lookup).

        Returns the latest value for each slot of the entity.
        Uses SlotIndex for constant-time lookups.

        Args:
            entity: Entity name to query (e.g., "alice")
            slot: Optional specific slot to query (e.g., "employer")

        Returns:
            Dict with:
                - entity: The queried entity name
                - found: Whether the entity exists
                - slots: Dict mapping slot names to their current values

        Example:
            >>> state = mem.state("alice")
            >>> if state["found"]:
            ...     print(f"Alice's employer: {state['slots'].get('employer', {}).get('value')}")
        """
        state_fn = getattr(self._core, "state", None)
        if state_fn is None:
            raise RuntimeError("state not available - feature not compiled")
        return state_fn(entity, slot)

    def enrich(
        self,
        *,
        engine: str = "rules",
        force: bool = False,
    ) -> Dict[str, Any]:
        """Run enrichment to extract memory cards from frames.

        Enrichment scans frame text to extract structured knowledge as
        memory cards (SPO triplets).

        Args:
            engine: Engine to use - "rules" (default, fast pattern-based).
                    For LLM enrichment, use the CLI: memvid enrich --engine llm
            force: Re-enrich all frames, ignoring previous enrichment records

        Returns:
            Dict with:
                - engine: Engine name used
                - version: Engine version
                - frames_processed: Number of frames enriched
                - cards_extracted: Number of new cards extracted
                - total_cards: Total cards after enrichment
                - total_entities: Total entities after enrichment
                - new_cards: Net new cards added

        Example:
            >>> result = mem.enrich()
            >>> print(f"Extracted {result['cards_extracted']} cards from {result['frames_processed']} frames")
        """
        enrich_fn = getattr(self._core, "enrich", None)
        if enrich_fn is None:
            raise RuntimeError("enrich not available - feature not compiled")
        return enrich_fn(engine, force)

    def export_facts(
        self,
        *,
        format: str = "json",
        entity: Optional[str] = None,
        with_provenance: bool = False,
    ) -> str:
        """Export memory cards (facts/triplets) to various formats.

        Args:
            format: Output format - "json" (default), "csv", or "ntriples"
            entity: Optional entity filter
            with_provenance: Include source frame info (source_frame_id, timestamp, engine)

        Returns:
            String in the requested format

        Example:
            >>> # Export all facts as JSON
            >>> json_data = mem.export_facts()
            >>>
            >>> # Export Alice's facts as CSV with provenance
            >>> csv_data = mem.export_facts(format="csv", entity="alice", with_provenance=True)
            >>>
            >>> # Export as N-Triples for RDF tools
            >>> ntriples = mem.export_facts(format="ntriples")
        """
        export_facts_fn = getattr(self._core, "export_facts", None)
        if export_facts_fn is None:
            raise RuntimeError("export_facts not available - feature not compiled")
        return export_facts_fn(format, entity, with_provenance)

    def add_memory_cards(
        self,
        cards: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Add memory cards (SPO triplets) directly.

        This allows manual addition of extracted facts, useful when using
        external LLM enrichment or custom extraction logic.

        For automated LLM enrichment, use the CLI: memvid enrich --engine claude

        Args:
            cards: List of dicts with keys:
                - entity (required): Subject of the fact
                - slot (required): Predicate/relationship
                - value (required): Object/value
                - kind (optional): "Fact", "Preference", "Event", "Profile", "Relationship", "Other"
                - polarity (optional): "Positive", "Negative", "Neutral"
                - source_frame_id (optional): Frame this fact was extracted from
                - engine (optional): Extraction engine name (default: "sdk")
                - engine_version (optional): Engine version (default: "1.0.0")

        Returns:
            Dict with 'added' count and 'ids' list

        Example:
            >>> mem.add_memory_cards([
            ...     {"entity": "Alice", "slot": "employer", "value": "Acme Corp", "kind": "Fact"},
            ...     {"entity": "Alice", "slot": "role", "value": "Engineer", "kind": "Profile"},
            ...     {"entity": "Bob", "slot": "friend", "value": "Alice", "kind": "Relationship", "polarity": "Positive"},
            ... ])
            {'added': 3, 'ids': [1, 2, 3]}
        """
        add_memory_cards_fn = getattr(self._core, "add_memory_cards", None)
        if add_memory_cards_fn is None:
            raise RuntimeError("add_memory_cards not available - feature not compiled")
        return add_memory_cards_fn(cards)


def use(
    kind: Kind,
    filename: str,
    apikey: Optional[ApiKey] = None,
    *,
    mode: str = "open",
    enable_vec: bool = False,
    enable_lex: bool = True,
    read_only: bool = False,
    force_writable: bool = False,
    lock_timeout_ms: int = 250,
    force: Optional[str] = None,
) -> Memvid:
    # Extract the actual API key string for _MemvidCore
    api_key_str = None
    if apikey is not None:
        if isinstance(apikey, str):
            api_key_str = apikey
        elif isinstance(apikey, dict):
            # If it's a dict, get the default key
            api_key_str = apikey.get("default")

    success = False
    try:
        core = _MemvidCore(
            filename,
            mode=mode,
            enable_lex=enable_lex,
            enable_vec=enable_vec,
            read_only=read_only,
            lock_timeout_ms=lock_timeout_ms,
            force=force,
            force_writable=force_writable,
            api_key=api_key_str,
        )
        normalized_apikey = _normalise_apikey(apikey)
        adapters = registry.resolve(str(kind), core, normalized_apikey)
        success = True
        return Memvid(kind=str(kind), core=core, attachments=adapters)
    finally:
        is_create = mode == "create"
        is_open = mode == "open" and success
        track_command(filename, mode, success, is_create and success, is_open)


def create(
    filename: str,
    *,
    kind: Kind = "basic",
    apikey: Optional[ApiKey] = None,
    enable_vec: bool = False,
    enable_lex: bool = True,
    memory_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Memvid:
    """Create a new Memvid file and return a façade handle.

    Args:
        filename: Path to the mv2 file to create
        kind: Adapter kind (default: "basic")
        apikey: API keys for LLM providers
        enable_vec: Enable vector index (default: False)
        enable_lex: Enable lexical index (default: True)
        memory_id: Dashboard memory ID to bind to (auto-syncs tickets)
        api_key: Memvid API key (required if memory_id provided, or use MEMVID_API_KEY env var)

    Returns:
        Memvid instance with plan capacity if memory_id was provided
    """
    # Resolve the Memvid API key (from param or env)
    memvid_api_key = api_key or os.environ.get("MEMVID_API_KEY")

    # Merge memvid_api_key into apikey for the core
    effective_apikey = apikey
    if memvid_api_key:
        if effective_apikey is None:
            effective_apikey = memvid_api_key
        elif isinstance(effective_apikey, str):
            # Keep the LLM key as-is, memvid_api_key will be passed separately
            pass

    mv = use(
        kind,
        filename,
        memvid_api_key if memvid_api_key else apikey,  # Pass memvid API key to core
        mode="create",
        enable_vec=enable_vec,
        enable_lex=enable_lex,
    )

    # Auto-sync tickets if memory_id is provided
    if memory_id:
        if not memvid_api_key:
            raise ApiKeyRequiredError(
                "memory_id requires api_key parameter or MEMVID_API_KEY environment variable. "
                "Get your API key at https://memvid.com/dashboard/api-keys"
            )
        # Convert 24-char MongoDB ObjectId to UUID format by padding with zeros
        normalized_id = memory_id.replace("-", "")
        if len(normalized_id) == 24 and all(c in "0123456789abcdefABCDEF" for c in normalized_id):
            normalized_id = normalized_id + "00000000"
        # Format as UUID with dashes
        if len(normalized_id) == 32:
            uuid_str = f"{normalized_id[:8]}-{normalized_id[8:12]}-{normalized_id[12:16]}-{normalized_id[16:20]}-{normalized_id[20:]}"
        else:
            uuid_str = memory_id  # Use as-is if already in UUID format
        # Get optional API URL from environment
        api_url = os.environ.get("MEMVID_DASHBOARD_URL")
        mv.sync_tickets(uuid_str, memvid_api_key, api_url)

    return mv


def lock(
    path: str,
    *,
    password: str,
    output: Optional[str] = None,
    force: bool = False,
) -> str:
    """Encrypt a `.mv2` file into an encrypted capsule (`.mv2e`)."""
    if _lock_capsule is None:
        raise RuntimeError("lock() support not available in this build")
    return str(_lock_capsule(path, password=password, output=output, force=force))


def unlock(
    path: str,
    *,
    password: str,
    output: Optional[str] = None,
    force: bool = False,
) -> str:
    """Decrypt a `.mv2e` capsule back into the original `.mv2` bytes."""
    if _unlock_capsule is None:
        raise RuntimeError("unlock() support not available in this build")
    return str(_unlock_capsule(path, password=password, output=output, force=force))


def lock_who(path: str) -> Dict[str, Any]:
    """Return lock status and owner information for a `.mv2` file."""
    if _lock_who is None:
        raise RuntimeError("lock_who support not available in this build")
    owner = _lock_who(path)
    return {"locked": owner is not None, "owner": owner}


def lock_nudge(path: str) -> bool:
    """Request a stale lock release for a `.mv2` file."""
    if _lock_nudge is None:
        raise RuntimeError("lock_nudge support not available in this build")
    return bool(_lock_nudge(path))


def verify_single_file(path: str) -> None:
    """Ensure no auxiliary files exist next to the `.mv2` (single-file guarantee)."""
    p = Path(path)
    parent = p.parent if p.parent != Path("") else Path(".")
    name = p.name
    offenders: List[str] = []
    for suffix in ("-wal", "-shm", "-lock", "-journal"):
        candidate = parent / f"{name}{suffix}"
        if candidate.exists():
            offenders.append(str(candidate))
    for suffix in (".wal", ".shm", ".lock", ".journal"):
        candidate = parent / f".{name}{suffix}"
        if candidate.exists():
            offenders.append(str(candidate))
    if not offenders:
        return
    err = CorruptFileError(
        "MV012: Auxiliary files detected next to the .mv2 (single-file guarantee violated)."
    )
    setattr(err, "code", "MV012")
    setattr(err, "offenders", offenders)
    raise err


def info() -> Dict[str, Any]:
    """Return SDK + native build information (for diagnostics and bug reports)."""
    try:
        from importlib import metadata as _metadata

        sdk_version = _metadata.version("memvid-sdk")
    except Exception:  # noqa: BLE001
        sdk_version = None

    native = _version_info() if callable(_version_info) else None
    return {
        "sdk_version": sdk_version,
        "platform": sys.platform,
        "python": sys.version.split()[0],
        "native": native,
        "native_exports": [k for k in dir(_lib) if not k.startswith("_")],
    }


__all__ = [
    # Main class
    "Memvid",
    # Factory functions
    "use",
    "create",
    "lock",
    "unlock",
    # Type aliases
    "Kind",
    # Base error
    "MemvidError",
    # Specific error classes (MV001-MV012)
    "CapacityExceededError",      # MV001
    "TicketInvalidError",         # MV002
    "TicketReplayError",          # MV003
    "LexIndexDisabledError",      # MV004
    "TimeIndexMissingError",      # MV005
    "VerifyFailedError",          # MV006
    "LockedError",                # MV007
    "ApiKeyRequiredError",        # MV008
    "MemoryAlreadyBoundError",    # MV009
    "FrameNotFoundError",         # MV010
    "VecIndexDisabledError",      # MV011
    "CorruptFileError",           # MV012
    "FileNotFoundError",          # MV013
    "VecDimensionMismatchError",  # MV014
    "EmbeddingFailedError",       # MV015
    "EncryptionError",            # MV016
    "NerModelNotAvailableError",  # MV017
    "ClipIndexDisabledError",     # MV018
    # Introspection helpers
    "lock_who",
    "lock_nudge",
    "verify_single_file",
    "info",
    # Embeddings module
    "embeddings",
    # Analytics (opt-out: MEMVID_TELEMETRY=0)
    "flush_analytics",
    "is_telemetry_enabled",
]


def _warn_deprecated(name: str) -> None:
    warnings.warn(
        f"memvid_sdk.{name}() is deprecated; use memvid_sdk.use('basic', path) instead",
        DeprecationWarning,
        stacklevel=3,
    )


def open(*args, **kwargs):  # type: ignore[override]
    _warn_deprecated("open")
    return _open(*args, **kwargs)


def put(*args, **kwargs):  # type: ignore[override]
    _warn_deprecated("put")
    return _put(*args, **kwargs)


def find(*args, **kwargs):  # type: ignore[override]
    _warn_deprecated("find")
    return _find(*args, **kwargs)


def ask(*args, **kwargs):  # type: ignore[override]
    _warn_deprecated("ask")
    return _ask(*args, **kwargs)
