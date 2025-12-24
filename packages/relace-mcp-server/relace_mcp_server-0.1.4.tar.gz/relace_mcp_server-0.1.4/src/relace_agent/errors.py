class AgentStop(BaseException):
    """Control flow mechanism to break out of an iterator."""


class AgentError(Exception):
    """Error during agent's operation."""


class BuildError(AgentError):
    """Error during site build."""


class TestError(AgentError):
    """Error during testing of generated site."""
