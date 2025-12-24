"""
Possible NUT Errors as specified in
https://networkupstools.org/docs/developer-guide.chunked/net-protocol.html#10-16-error-responses
"""

from enum import Enum


class NutError(Enum):
    AccessDenied = "ACCESS-DENIED"
    UnknownUps = "UNKNOWN-UPS"
    VarNotSupported = "VAR-NOT-SUPPORTED"
    CmdNotSupported = "CMD-NOT-SUPPORTED"
    InvalidArgument = "INVALID-ARGUMENT"
    InstcmdFailed = "INSTCMD-FAILED"
    SetFailed = "SET-FAILED"
    Readonly = "READONLY"
    TooLong = "TOO-LONG"
    FeatureNotSupported = "FEATURE-NOT-SUPPORTED"
    FeatureNotConfigured = "FEATURE-NOT-CONFIGURED"
    AlreadySslMode = "ALREADY-SSL-MODE"
    DriverNotConnected = "DRIVER-NOT-CONNECTED"
    DataStale = "DATA-STALE"
    AlreadyLoggedIn = "ALREADY-LOGGED-IN"
    InvalidPassword = "INVALID-PASSWORD"
    AlreadySetPassword = "ALREADY-SET-PASSWORD"
    InvalidUsername = "INVALID-USERNAME"
    AlreadySetUsername = "ALREADY-SET-USERNAME"
    UsernameRequired = "USERNAME-REQUIRED"
    PasswordRequired = "PASSWORD-REQUIRED"
    UnknownCommand = "UNKNOWN-COMMAND"
    InvalidValue = "INVALID-VALUE"


def build_nut_error(e: NutError):
    return f"ERR {e.value}"
