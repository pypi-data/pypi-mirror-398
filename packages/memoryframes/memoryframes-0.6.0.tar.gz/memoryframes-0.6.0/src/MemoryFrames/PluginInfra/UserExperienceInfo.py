import sys


# ----------------------------------------------------------------------
class UserExperienceInfo:
    """Abstract base class for information associated with user experiences.

    This information is passed to a Plugin on creation, where it uses the info to adjust its behavior
    based on the information's derived type and associated data.
    """

    # ----------------------------------------------------------------------
    def __init__(self) -> None:
        # Ensure that only known classes inherit from this base class, as it is not a small thing
        # to introduce a new user experience type (as all plugins, across the world, must be
        # updated to support it.
        if not sys.flags.optimize:
            # Avoid circular import issues by importing here
            from MemoryFrames.PluginInfra.TextualUserExperienceInfo import TextualUserExperienceInfo  # noqa: PLC0415

            assert isinstance(
                self,
                (TextualUserExperienceInfo,),
            ), self
