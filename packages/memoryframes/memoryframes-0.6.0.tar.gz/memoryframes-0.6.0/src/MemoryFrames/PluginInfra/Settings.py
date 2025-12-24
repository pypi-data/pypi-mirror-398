from typing import cast, TYPE_CHECKING

import rtyaml


if TYPE_CHECKING:
    from pathlib import Path

    from MemoryFrames.PluginInfra.Plugin import Plugin


# ----------------------------------------------------------------------
class Settings:
    """Settings used by MemoryFrames and its plugins."""

    # ----------------------------------------------------------------------
    @classmethod
    def DeserializeOrCreate(
        cls,
        content_dir: Path,
        working_dir: Path,
        *,
        verbose: bool,
        debug: bool,
    ) -> Settings:
        """Deserialize settings from disk or create default settings if necessary."""

        settings_filename = cls._GetSettingsFilename(working_dir)

        if settings_filename.is_file():
            with settings_filename.open("r", encoding="utf-8") as f:
                settings = rtyaml.load(f)
        else:
            settings = {}

        return cls(
            content_dir,
            working_dir,
            cast(dict[str, object], settings),
            verbose=verbose,
            debug=debug,
        )

    # ----------------------------------------------------------------------
    def __init__(
        self,
        content_dir: Path,
        working_dir: Path,
        settings: dict[str, object],
        *,
        verbose: bool,
        debug: bool,
    ) -> None:
        if debug is True:
            verbose = True

        # Commit results
        self.content_dir = content_dir
        self.working_dir = working_dir

        self.verbose = verbose
        self.debug = debug

        self._settings = settings

    # ----------------------------------------------------------------------
    def Serialize(self) -> None:
        """Serialize settings to disk."""

        settings_filename = self._GetSettingsFilename(self.working_dir)

        with settings_filename.open("w", encoding="utf-8") as f:
            rtyaml.dump(self._settings, f)

    # ----------------------------------------------------------------------
    def GetPluginSettings(self, plugin: type[Plugin]) -> dict[str, object]:
        """Return the settings associated with the provided Plugin."""

        return cast(dict[str, object], self._settings.get(f"{plugin.AUTHOR}_{plugin.NAME}", {}))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _GetSettingsFilename(working_dir: Path) -> Path:
        return working_dir / "settings.yaml"
