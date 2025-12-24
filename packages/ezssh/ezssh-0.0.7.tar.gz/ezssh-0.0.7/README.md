# EZSSH

#### An Ergonomic and Lightweight SSH Library.

## Installation

``` bash
pip install ezssh
```

## Quick Start

``` python
from ezssh import SSHRunner, Command, BatchPolicy

with SSHRunner(
    host="10.0.0.5",
    username="ubuntu",
    password="secret", # password as null will attempt pubkey
) as runner:

    result = runner.run("uname -a")
    print(result.stdout)

    batch = runner.run_batch(
        [
            "whoami",
            Command("systemctl is-active ssh", sudo=True, name="ssh_status"),
        ],
        policy=BatchPolicy(stop_on_failure=False),
    )

    for r in batch.results:
        print(r.command.name, r.exit_status)

```

## Batch Operations
batch processing of cli commands is also available. To execute a chain of prepared commands:

``` python
batch = runner.run_batch(
    [
        Command("mkdir -p /tmp/example"),
        Command("touch /tmp/example/file.txt"),
        Command("false", name="intentional_failure"),
        Command("echo still runs"),
    ],
    policy=BatchPolicy(stop_on_failure=False),
)
# Each returns an exit status, stdout/stderror, start/end and duration.
```

## Authentication Behavior
Password auth uses password only, agent and key discovery are opt-in.
```python
SSHRunner(
    host="example.com",
    username="user",
    password="secret",
    allow_agent=False,
    look_for_keys=False,
)
```

## When to Use ezssh

Use ezssh if you need:
- Programmatic SSH execution embedded in a Python application
- Deterministic batch execution with structured results
- Explicit authentication behavior
- Lightweight automation without orchestration frameworks

Do not use ezssh if you need:
- Configuration management
- Long-lived agents
- Inventory management
- Declarative state convergence

## How ezssh Compares

| Tool     | ezssh | Paramiko | Fabric | Ansible |
|----------|-------|----------|--------|---------|
| Embedded in apps | ✅ | ⚠️ | ⚠️ | ❌ |
| Batch semantics | ✅ | ❌ | ⚠️ | ✅ |
| Explicit auth | ✅ | ❌ | ❌ | ⚠️ |
| Minimal deps | ✅ | ✅ | ❌ | ❌ |
| YAML required | ❌ | ❌ | ❌ | ✅ |
