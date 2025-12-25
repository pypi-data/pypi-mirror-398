from sayou.core.exceptions import SayouCoreError


class AssemblerError(SayouCoreError):
    """Base exception for assembler errors."""

    pass


class BuildError(AssemblerError):
    """Raised when assembly logic fails."""

    pass
