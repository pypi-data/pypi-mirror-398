from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import auto, Enum
from typing import TYPE_CHECKING

import pluggy

from MemoryFrames import APP_NAME
from MemoryFrames.PluginInfra import Plugin as PluginModule

if TYPE_CHECKING:
    from MemoryFrames.PluginInfra.Plugin import Plugin
    from MemoryFrames.PluginInfra.Settings import Settings
    from MemoryFrames.PluginInfra.UserExperienceInfo import UserExperienceInfo


# ----------------------------------------------------------------------
class AppStateObserver(ABC):
    """Observer for AppState changes."""

    # ----------------------------------------------------------------------
    class EventType(Enum):
        """Value signaling progress during the creation of an AppState instance."""

        LoadingPlugins = auto()

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnEvent(self, event_type: EventType) -> None:
        """Invoke when a processing event begins."""
        raise NotImplementedError()  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnException(self, exception: Exception) -> None:
        """Invoke when an exception occurs during processing."""
        raise NotImplementedError()  # pragma: no cover


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class AppState:
    """MemoryFrames application state."""

    # ----------------------------------------------------------------------
    plugins: list[Plugin]

    # ----------------------------------------------------------------------
    @classmethod
    def Create(
        cls,
        settings: Settings,
        user_experience_info: UserExperienceInfo,
        observer: AppStateObserver,
    ) -> AppState | None:
        """Create an AppState instance."""

        # Load the plugins
        observer.OnEvent(AppStateObserver.EventType.LoadingPlugins)

        try:
            plugins = LoadPlugins(settings, user_experience_info)
        except Exception as ex:
            observer.OnException(ex)
            return None

        # We want the highest priority plugins first, and then sort by name. We apply the negative so
        # that higher priority values appear first while still maintaining ascending order for names.
        plugins.sort(key=lambda plugin: (-(plugin.PLUGIN_PRIORITY or 0), plugin.NAME))

        return cls(plugins)


# ----------------------------------------------------------------------
def LoadPlugins(
    settings: Settings,
    user_experience_info: UserExperienceInfo,
) -> list[Plugin]:
    """Load the plugins.

    This is implemented as a separate function to make it easier to monkey-patch during testing.
    """

    plugin_manager = pluggy.PluginManager(APP_NAME)

    plugin_manager.add_hookspecs(PluginModule)
    plugin_manager.load_setuptools_entrypoints(APP_NAME)

    plugins: list[Plugin] = plugin_manager.hook.GetPlugin(
        settings=settings,
        user_experience_info=user_experience_info,
    )

    return plugins
