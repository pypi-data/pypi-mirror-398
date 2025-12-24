from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MemoryFrames.PluginInfra.Note import Note


# ----------------------------------------------------------------------
class NoteSource:
    """Base class for a plugin component that provides notes to MemoryFrames."""

    # ----------------------------------------------------------------------
    def __init__(self, observer: NoteSourceObserver) -> None:
        self.observer = observer


# ----------------------------------------------------------------------
class NoteSourceObserver(ABC):
    """Base class for an observer that receives event notifications from a NoteSource."""

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnNewNote(
        self,
        note: Note,
        *,
        is_initializing: bool,
    ) -> None:
        """Indicate that a note has been discovered."""
        raise NotImplementedError()  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnInitializationComplete(self, note_source: NoteSource) -> None:
        """Indicate that the NoteSource has completed its initialization."""
        raise NotImplementedError()  # pragma: no cover
