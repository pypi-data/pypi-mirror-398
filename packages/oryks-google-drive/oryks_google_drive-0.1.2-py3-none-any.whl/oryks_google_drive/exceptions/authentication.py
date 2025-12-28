class YouTubeOAuthException(Exception):
    """The base exception for all authentication exceptions."""


class MissingClientSecretsFile(YouTubeOAuthException):
    """Raised when trying to authenticate a request without providing the client secrets file."""


class InvalidSecretsFileError(YouTubeOAuthException):
    """Raised when the secrets file is invalid."""
