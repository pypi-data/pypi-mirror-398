import traceback

from pathlib import Path
from typing import TYPE_CHECKING

from dbrownell_Common.Types import override
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Label, LoadingIndicator

from MemoryFrames import APP_NAME, __version__
from MemoryFrames.AppState import AppState, AppStateObserver as AppStateObserverBase
from MemoryFrames.PluginInfra.TextualUserExperienceInfo import TextualUserExperienceInfo

if TYPE_CHECKING:
    from MemoryFrames.PluginInfra.Settings import Settings


# ----------------------------------------------------------------------
def Execute(settings: Settings) -> None:
    """Execute the Textual user experience."""

    _App(settings).run()


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class _App(App):
    CSS_PATH = Path(__file__).with_suffix(".tcss")

    # ----------------------------------------------------------------------
    def __init__(self, settings: Settings) -> None:
        super().__init__()

        self._settings = settings

        self._user_experience = TextualUserExperienceInfo(
            self.app,
            VerticalScroll(id="hierarchies"),
        )

        # The app state is initialized in `on_mount`
        self._app_state: AppState | None = None

        self.title = "Memory Frames"
        assert self.title.replace(" ", "") == APP_NAME, (self.title, APP_NAME)

    # ----------------------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="viewport"):
            yield self._user_experience.hierarchy_container

        with Horizontal(id="footer"):
            yield Footer()
            yield Label(__version__)

    # ----------------------------------------------------------------------
    def on_mount(self) -> None:
        # ----------------------------------------------------------------------
        def OnLoaded(app_state: AppState | None) -> None:
            if app_state is None:
                return

            assert self._app_state is None
            self._app_state = app_state

        # ----------------------------------------------------------------------

        self.push_screen(
            _LoadingModal(self._settings, self._user_experience),
            OnLoaded,
        )


# ----------------------------------------------------------------------
class _LoadingModal(ModalScreen[AppState]):
    CSS_PATH = Path(__file__).with_suffix(".tcss")

    # ----------------------------------------------------------------------
    def __init__(
        self,
        settings: Settings,
        user_experience_info: TextualUserExperienceInfo,
    ) -> None:
        super().__init__()

        self._settings = settings
        self._user_experience_info = user_experience_info

        self._status_label = Label("Loading...")

    # ----------------------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield LoadingIndicator()
        yield self._status_label

    # ----------------------------------------------------------------------
    def on_mount(self) -> None:
        loading_module = self

        # ----------------------------------------------------------------------
        def Execute() -> None:
            current_event: AppStateObserverBase.EventType | None = None

            # ----------------------------------------------------------------------
            class AppStateObserver(AppStateObserverBase):
                # ----------------------------------------------------------------------
                @override
                def OnEvent(self, event_type: AppStateObserver.EventType) -> None:
                    nonlocal current_event
                    current_event = event_type

                    if event_type == AppStateObserver.EventType.LoadingPlugins:
                        msg = "Loading plugins..."
                    elif event_type == AppStateObserver.EventType.StartingThreads:
                        msg = "Starting threads..."
                    else:
                        assert False, event_type  # noqa: B011, PT015

                    loading_module._status_label.content = msg  # noqa: SLF001

                # ----------------------------------------------------------------------
                @override
                def OnException(self, exception: Exception) -> None:
                    if loading_module._settings.debug:  # noqa: SLF001
                        msg = "".join(traceback.format_exception(exception))
                    else:
                        msg = str(exception)

                    if current_event == AppStateObserver.EventType.LoadingPlugins:
                        loading_module.app.panic(msg)
                        return

                    # Display in a toast
                    loading_module.notify(msg, severity="error", timeout=10)

            # ----------------------------------------------------------------------

            app_state = AppState.Create(self._settings, self._user_experience_info, AppStateObserver())

            # Return the results
            self.app.call_from_thread(lambda: self.dismiss(app_state))

        # ----------------------------------------------------------------------

        self.run_worker(Execute, thread=True)
