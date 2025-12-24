# src/paramiko_batch/exceptions.py
class SSHBatchError(Exception):
    """Base exception for this library."""

class SSHConnectionError(SSHBatchError):
    pass

class SSHCommandError(SSHBatchError):
    """Raised optionally when stop_on_failure triggers."""
    def __init__(self, message: str, exit_status: int | None = None):
        super().__init__(message)
        self.exit_status = exit_status
