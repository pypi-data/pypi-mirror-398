from typing import TYPE_CHECKING

from MemoryFrames.PluginInfra.UserExperienceInfo import UserExperienceInfo

if TYPE_CHECKING:
    from textual.app import App
    from textual.containers import VerticalScroll


# ----------------------------------------------------------------------
class TextualUserExperienceInfo(UserExperienceInfo):
    """User experience that leverages Textual for TUI capabilities."""

    # ----------------------------------------------------------------------
    def __init__(
        self,
        app: App,
        hierarchy_container: VerticalScroll,
    ) -> None:
        super().__init__()

        self.app = app
        self.hierarchy_container = hierarchy_container
