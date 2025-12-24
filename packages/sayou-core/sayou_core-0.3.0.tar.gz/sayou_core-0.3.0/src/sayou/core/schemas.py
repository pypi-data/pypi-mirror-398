from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ==============================================================================
# 1. Ingestion Stage (Connector)
# ==============================================================================
class SayouTask(BaseModel):
    """
    [Input] Defines a unit of work for the Connector.

    Generators produce these tasks (e.g., "Download this URL"), and Fetchers
    execute them.
    """

    source_type: str = Field(..., description="Routing key (e.g., 'file', 'http')")
    uri: str = Field(..., description="Resource location")
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Execution parameters"
    )
    meta: Dict[str, Any] = Field(default_factory=dict, description="Context metadata")


class SayouPacket(BaseModel):
    """
    [Transport] The universal container for raw data transport.

    Produced by Connector, this packet carries the raw payload (bytes, str, or dict)
    safely across the pipeline boundaries.
    """

    task: Optional[SayouTask] = Field(
        None, description="The task that originated this packet"
    )
    data: Any = Field(None, description="Raw payload (Bytes, String, or Dict)")
    success: bool = Field(True, description="Operation status")
    error: Optional[str] = Field(None, description="Error message if failed")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Process metadata")
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True


# ==============================================================================
# 2. Refinement Stage (Refinery Output)
# ==============================================================================
class SayouBlock(BaseModel):
    """
    [Intermediate] The atomic unit of content (Text/Image/Record).

    Refinery normalizes raw data into these blocks. Chunking splits these blocks
    into smaller pieces.
    """

    type: str = Field(
        ..., description="Content type (e.g., 'text', 'md', 'record', 'image')"
    )
    content: Union[str, Dict[str, Any], List[Any]] = Field(
        ..., description="Actual content payload"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Source context (page, lineage)"
    )


# ==============================================================================
# 3. Chunking Stage (Chunking Output)
# ==============================================================================
class SayouChunk(BaseModel):
    """
    [Intermediate] The segmented text unit ready for Embedding.

    Chunking splits a `SayouBlock` into multiple `SayouChunk`s.
    """

    content: str = Field(..., description="The split text segment")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Context (chunk_id, parent_id, source)"
    )

    def update_metadata(self, **kwargs):
        """Helper to update metadata in-place."""
        self.metadata.update(kwargs)


# ==============================================================================
# 3. Knowledge Graph Stage (Wrapper / Assembler / Loader)
# ==============================================================================
class SayouNode(BaseModel):
    """
    [Atom] The standard knowledge entity ready for Graph/Vector DB.

    Wrapper converts chunks into these nodes, assigning Ontology classes
    and identifying relationships.
    """

    node_id: str = Field(..., description="Unique Identifier (URI)")
    node_class: str = Field(..., description="Ontology Class (e.g., 'sayou:Topic')")
    friendly_name: Optional[str] = Field(None, description="Human-readable label")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Properties/Values"
    )
    relationships: Dict[str, List[str]] = Field(
        default_factory=dict, description="Links to other nodes"
    )
    vector: Optional[List[float]] = Field(
        None, description="Embedding vector (optional)"
    )


class SayouOutput(BaseModel):
    """
    [Output] The final container for assembled knowledge.

    Contains a collection of SayouNodes and global metadata. This is what
    Sayou Assembler produces and Sayou Loader consumes. (Formerly 'WrapperOutput')
    """

    nodes: List[SayouNode] = Field(default_factory=list, description="List of entities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Global context")
