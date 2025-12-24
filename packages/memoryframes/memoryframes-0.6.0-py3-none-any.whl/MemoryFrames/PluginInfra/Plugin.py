from dataclasses import dataclass
from functools import cached_property
from typing import ClassVar, TYPE_CHECKING

import pluggy

from MemoryFrames import APP_NAME

if TYPE_CHECKING:
    from collections.abc import Callable
    from threading import Event
    from pathlib import Path

    from MemoryFrames.PluginInfra.NoteSource import NoteSource, NoteSourceObserver
    from MemoryFrames.PluginInfra.Settings import Settings
    from MemoryFrames.PluginInfra.UserExperienceInfo import UserExperienceInfo


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class ThreadInfo:
    """Information about a thread that is defined by a Plugin but created and managed by the application."""

    description: str
    thread_func: Callable[
        [
            Event  # Event set when the application is quitting
        ],
        None,
    ]


# ----------------------------------------------------------------------
class Plugin:
    """Base class for all MemoryFrames plugins."""

    # ----------------------------------------------------------------------
    NAME: ClassVar[str] = ""
    """The name of the plugin."""

    AUTHOR: ClassVar[str] = ""
    """The author of the plugin. This value will be used in the plugin's unique name."""

    DESCRIPTION: ClassVar[str] = ""
    """The description of the plugin."""

    PLUGIN_PRIORITY: ClassVar[int] = 0
    """The priority of the plugin. Higher values indicate higher priority, which will cause the plugin to appear before other lower priority plugins."""

    # ----------------------------------------------------------------------
    def __init__(
        self,
        root_data_dir: Path,
    ) -> None:
        assert self.__class__.NAME, "Derived classes must set the NAME class variable"
        assert self.__class__.AUTHOR, "Derived classes must set the AUTHOR class variable"
        assert self.__class__.DESCRIPTION, "Derived classes must set the DESCRIPTION class variable"

        scrubbed_unique_name = self.unique_name

        for invalid_char in ["<", ">", ":", '"', "/", "\\", "|", "?", "*", "."]:
            scrubbed_unique_name = scrubbed_unique_name.replace(invalid_char, "_")

        self.working_dir = root_data_dir / scrubbed_unique_name

    # ----------------------------------------------------------------------
    @cached_property
    def unique_name(self) -> str:
        """The unique name of the plugin."""
        return f"{self.__class__.AUTHOR}_{self.__class__.NAME}"

    # ----------------------------------------------------------------------
    def GetNoteSource(
        self,
        observer: NoteSourceObserver,  # noqa: ARG002
        enqueue_thread_info_func: Callable[[ThreadInfo], None],  # noqa: ARG002
    ) -> NoteSource | None:
        """Return a NoteSource implemented by this plugin."""
        return None


# ----------------------------------------------------------------------
@pluggy.HookspecMarker(APP_NAME)
def GetPlugin(
    settings: Settings,
    user_experience_info: UserExperienceInfo,
) -> Plugin:
    """Return a Plugin instance."""
    raise NotImplementedError()  # pragma: no cover
