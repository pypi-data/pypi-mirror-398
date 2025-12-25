from sayou.core.exceptions import SayouCoreError


class WrapperError(SayouCoreError):
    """Base exception for wrapper errors."""

    pass


class AdaptationError(WrapperError):
    """Raised when adaptation logic fails."""

    pass
