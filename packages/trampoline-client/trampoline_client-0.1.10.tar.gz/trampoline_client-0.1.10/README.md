# Trampoline Client

Python client for [Trampoline](https://github.com/rlange/trampoline) dynamic reverse proxy.

## Installation

```bash
pip install trampoline-client
```

## Usage

```python
from trampoline_client import TrampolineClient
import time

client = TrampolineClient(
    host="wss://t.example.com",
    name="myservice",  # alphanumeric only, no dashes
    secret="your-secret",
    target="http://localhost:3000"
)

client.start()
time.sleep(1)

if client.connected:
    print(f"Worker {client.worker_index} at: {client.remote_address}")
    # https://myservice-0.t.example.com (specific worker)
    print(f"Pool address: {client.remote_address_roundrobin}")
    # https://myservice.t.example.com (round-robin)

client.stop()
```

## Load Balancing

```python
for i in range(3):
    client = TrampolineClient(
        host="wss://t.example.com",
        name="myservice",  # alphanumeric only
        existing_ok=True,  # Join existing pool
        target="http://localhost:3000"
    )
    client.start()
    # Workers get indices 0, 1, 2
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `host` | Server URL (base domain) | (required) |
| `name` | Tunnel name (alphanumeric only, no dashes) | (required) |
| `secret` | Auth secret | `None` |
| `target` | Local server to forward to | `http://localhost:80` |
| `existing_ok` | Join existing pool | `False` |
| `verify_ssl` | Verify SSL certificates | `True` |
| `max_retries` | Max reconnection attempts (0=infinite) | `5` |
| `retry_delay` | Initial retry delay in seconds | `5.0` |
| `daemon` | Daemon thread | `True` |

## Properties

| Property | Description |
|----------|-------------|
| `connected` | Connection active |
| `worker_index` | Assigned worker index (0, 1, 2...) |
| `remote_address` | Worker-specific URL (`https://name-N.domain`) |
| `remote_address_roundrobin` | Pool URL (`https://name.domain`) |
| `pool_size` | Workers in pool |
| `reconnect_count` | Reconnection attempts |

## License

MIT
