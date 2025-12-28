class YouTubeOAuthorizationException(Exception):
    """The base exception for all authorization exceptions."""


class ForbiddenError(Exception):
    """
    The request cannot access user rating information. This error may occur because the request is not properly
    authorized to use the myRating parameter.
    The request is not properly authorized to access video file or processing information. Note that the fileDetails,
    processingDetails, and suggestions parts are only available to that video's owner.
    """
