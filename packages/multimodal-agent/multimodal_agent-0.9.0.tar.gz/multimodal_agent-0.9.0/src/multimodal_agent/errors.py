class AgentError(Exception):
    """
    Base exception for all multimodal-agent errors.
    """


class RetryableError(AgentError):
    """
    Error that should be tried again.
    Typically raised on 503 model overload or transient network issues.
    """


class NonRetryableError(AgentError):
    """
    Error that should not be tried again.
    Usually raised for invalid input or configuration issues.
    """


class InvalidImageError(NonRetryableError):
    """
    Raised when an image cannot be read or converted into a Part.
    """


class ConfigError(NonRetryableError):
    """
    Raised when required environment variables or configuration is missing.
    """
