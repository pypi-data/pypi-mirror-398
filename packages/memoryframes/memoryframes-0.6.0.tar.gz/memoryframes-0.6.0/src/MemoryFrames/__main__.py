import os

from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from typer.core import TyperGroup

from MemoryFrames import TextualUserExperience
from MemoryFrames.PluginInfra.Settings import Settings


# ----------------------------------------------------------------------
class NaturalOrderGrouper(TyperGroup):  # noqa: D101
    # ----------------------------------------------------------------------
    def list_commands(self, *args, **kwargs) -> list[str]:  # noqa: ARG002, D102
        return list(self.commands.keys())  # pragma: no cover


# ----------------------------------------------------------------------
app = typer.Typer(
    cls=NaturalOrderGrouper,
    help=__doc__,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
)


# ----------------------------------------------------------------------
def _GetWorkingDir() -> Path:
    data_dir = Path.home()

    if os.name == "nt":  # noqa: SIM108
        data_dir = data_dir / "AppData" / "Local"
    else:
        data_dir = data_dir / ".local" / "share"

    data_dir /= "MemoryFrames"

    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir


# ----------------------------------------------------------------------
class _ExperienceType(str, Enum):
    Textual = "Textual"


# ----------------------------------------------------------------------
@app.command("EntryPoint", no_args_is_help=False)
def EntryPoint(
    content_dir: Annotated[
        Path,
        typer.Option(
            "--content-dir",
            exists=True,
            file_okay=False,
            help="Directory containing notes to load.",
            resolve_path=True,
        ),
    ] = Path.cwd(),  # noqa: B008
    working_dir: Annotated[
        Path,
        typer.Option(
            "--working-dir",
            file_okay=False,
            help="Directory to use for settings and other persisted data.",
            resolve_path=True,
        ),
    ] = _GetWorkingDir(),  # noqa: B008
    experience: Annotated[
        _ExperienceType,
        typer.Option("--experience", case_sensitive=False, help="The user experience to use."),
    ] = _ExperienceType.Textual,
    verbose: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--verbose", help="Write verbose information to the terminal."),
    ] = False,
    debug: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--debug", help="Write debug information to the terminal."),
    ] = False,
) -> None:
    """Run MemoryFrames."""

    content_dir.mkdir(parents=True, exist_ok=True)
    working_dir.mkdir(parents=True, exist_ok=True)

    settings = Settings.DeserializeOrCreate(content_dir, working_dir, verbose=verbose, debug=debug)

    if experience == _ExperienceType.Textual:
        user_experience_func = TextualUserExperience.Execute
    else:
        assert False, experience  #  noqa: B011, PT015  # pragma: no cover

    user_experience_func(settings)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()  # pragma: no cover
