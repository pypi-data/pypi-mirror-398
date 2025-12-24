# src/paramiko_batch/client.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Sequence, Union
import shlex
import time

import paramiko

from .models import Command, CommandResult, BatchPolicy, BatchResult
from .exceptions import SSHConnectionError, SSHCommandError

def _compose_command(c: Command) -> str:
    """
    Build a remote shell string that supports env + cwd + sudo.
    Note: this uses shell concatenation; for hostile input, callers should be careful.
    """
    parts = []
    if c.env:
        # export KEY=VALUE ...
        exports = " ".join(f"{k}={shlex.quote(v)}" for k, v in c.env.items())
        parts.append(f"export {exports}")
    if c.cwd:
        parts.append(f"cd {shlex.quote(c.cwd)}")
    cmd = c.cmd
    if c.sudo:
        # -n: non-interactive, fail if password required
        cmd = f"sudo -n -- {cmd}"
    parts.append(cmd)
    return " && ".join(parts) if len(parts) > 1 else parts[0]

@dataclass
class SSHRunner:
    host: str
    username: str
    port: int = 22
    pkey: Optional[paramiko.PKey] = None
    password: Optional[str] = None
    known_hosts: Optional[str] = None  # path if you want
    missing_host_key_policy: str = "reject"  # "autoadd" | "reject"
    connect_timeout: float = 10.0

    _client: Optional[paramiko.SSHClient] = None

    def connect(self) -> "SSHRunner":
        print(
            self.username,
            self
        )
        try:
            client = paramiko.SSHClient()
            use_password = self.password is not None

            if self.missing_host_key_policy == "autoadd":
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            else:
                client.set_missing_host_key_policy(paramiko.RejectPolicy())

            if self.known_hosts:
                client.load_host_keys(self.known_hosts)
            else:
                client.load_system_host_keys()

            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                pkey=self.pkey,
                password=self.password,
                timeout=self.connect_timeout,
                banner_timeout=self.connect_timeout,
                auth_timeout=self.connect_timeout,
                look_for_keys=(not use_password and self.pkey is None),
                allow_agent=(not use_password and self.pkey is None)
            )

            self._client = client
            return self
        except Exception as e:
            print(e)
            raise SSHConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}") from e

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "SSHRunner":
        return self.connect()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def run(self, cmd: Union[str, Command], timeout: Optional[float] = None) -> CommandResult:
        if self._client is None:
            raise SSHConnectionError("Not connected. Use SSHRunner(...).connect() or context manager.")

        command = cmd if isinstance(cmd, Command) else Command(cmd=cmd, timeout=timeout)

        started = time.time()
        remote = _compose_command(command)

        # get_pty is sometimes required if sudo prompts, but we use sudo -n to avoid prompts
        stdin, stdout, stderr = self._client.exec_command(remote, timeout=command.timeout)

        # Paramiko's exec_command timeout is a socket timeout, not a hard kill.
        # We'll still read until exit status is available or channel indicates completion.
        exit_status = stdout.channel.recv_exit_status()

        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
        finished = time.time()

        return CommandResult(
            command=command,
            exit_status=exit_status,
            stdout=out,
            stderr=err,
            started_at=started,
            finished_at=finished,
        )

    def run_batch(
        self,
        commands: Sequence[Union[str, Command]],
        policy: BatchPolicy = BatchPolicy(stop_on_failure=True),
    ) -> BatchResult:
        batch = BatchResult()

        for item in commands:
            c = item if isinstance(item, Command) else Command(cmd=str(item))
            result = self.run(c)
            batch.results.append(result)

            if policy.stop_on_failure and not result.ok:
                raise SSHCommandError(
                    message=f"Command failed: {c.name or c.cmd}",
                    exit_status=result.exit_status,
                )

        return batch
