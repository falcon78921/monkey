class FailedExploitationError(Exception):
    """Raise when exploiter fails instead of returning False"""


class InvalidRegistrationCredentialsError(Exception):
    """Raise when server config file changed and island needs to restart"""


class AlreadyRegisteredError(Exception):
    """Raise to indicate the reason why registration is not required"""


class UnknownUserError(Exception):
    """Raise to indicate that authentication failed"""


class IncorrectCredentialsError(Exception):
    """Raise to indicate that authentication failed"""


class NoInternetError(Exception):
    """Raise to indicate problems caused when no internet connection is present"""


class DomainControllerNameFetchError(FailedExploitationError):
    """Raise on failed attempt to extract domain controller's name"""
