from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from MemoryFrames.PluginInfra.NoteSource import NoteSource


# ----------------------------------------------------------------------
@dataclass
class Note:
    """A note."""

    id: UUID

    source: NoteSource
    source_data: object
    """Opaque data provided by the NoteSource that created the note."""

    metadata: dict[str, object] = field(repr=False)
    content: str = field(repr=False)

    metadata_hash: bytes = field(repr=False)
    content_hash: bytes = field(repr=False)
