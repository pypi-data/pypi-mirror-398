from __future__ import annotations


class ColabError(Exception):
    pass


class AuthenticationError(ColabError):
    pass


class TokenExpiredError(AuthenticationError):
    pass


class TokenRefreshError(AuthenticationError):
    pass


class ServerError(ColabError):
    pass


class ServerNotAssignedError(ServerError):
    pass


class ServerAssignmentError(ServerError):
    pass


class QuotaDeniedError(ServerAssignmentError):
    pass


class UsageQuotaExceededError(ServerAssignmentError):
    pass


class AccountBlockedError(ServerAssignmentError):
    pass


class SessionError(ColabError):
    pass


class KernelError(ColabError):
    pass


class KernelNotReadyError(KernelError):
    pass


class ExecutionError(ColabError):
    pass


class ExecutionTimeoutError(ExecutionError):
    pass


class WebSocketError(ColabError):
    pass
