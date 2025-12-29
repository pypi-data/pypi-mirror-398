# PyLet

[![PyPI version](https://img.shields.io/pypi/v/pylet.svg)](https://pypi.org/project/pylet/)
[![Python versions](https://img.shields.io/pypi/pyversions/pylet.svg)](https://pypi.org/project/pylet/)
[![License](https://img.shields.io/pypi/l/pylet.svg)](https://github.com/ServerlessLLM/pylet/blob/main/LICENSE)

A simple distributed task execution system for GPU servers. Like Ray/K8s but much simpler.

## Install

```bash
pip install pylet
```

For development:

```bash
git clone https://github.com/ServerlessLLM/pylet.git
cd pylet
pip install -e ".[dev]"
```

## Quick Start

### CLI

```bash
# Terminal 1: Start head node
pylet start

# Terminal 2: Start worker node with GPUs
pylet start --head localhost:8000 --gpu-units 4

# Terminal 3: Submit an instance
pylet submit 'vllm serve Qwen/Qwen2.5-1.5B-Instruct --port $PORT' \
    --gpu-units 1 --name my-vllm

# Check status
pylet get-instance --name my-vllm

# Get endpoint for inference
pylet get-endpoint --name my-vllm
# Output: 192.168.1.10:15600

# View logs
pylet logs <instance-id>

# Cancel
pylet cancel <instance-id>
```

### Python API

```python
import pylet

# Connect to head node
pylet.init()  # or pylet.init("http://head:8000")

# Submit an instance
instance = pylet.submit(
    "vllm serve Qwen/Qwen2.5-1.5B-Instruct --port $PORT",
    name="my-vllm",
    gpu=1,
    memory=4096,
)

# Wait for it to start
instance.wait_running()
print(f"Endpoint: {instance.endpoint}")

# Get logs
print(instance.logs())

# Cancel when done
instance.cancel()
instance.wait()
```

For local testing:

```python
import pylet

with pylet.local_cluster(workers=2, gpu_per_worker=1) as cluster:
    instance = pylet.submit("nvidia-smi", gpu=1)
    instance.wait()
    print(instance.logs())
```

Async API available via `import pylet.aio as pylet`.

See [examples/README.md](examples/README.md) for more detailed examples including vLLM and SGLang.

## Commands

| Command | Description |
|---------|-------------|
| `pylet start` | Start head node |
| `pylet start --head <ip:port> --gpu-units N` | Start worker with N GPUs |
| `pylet submit <cmd> --gpu-units N --name <name>` | Submit instance |
| `pylet get-instance --name <name>` | Get instance status |
| `pylet get-endpoint --name <name>` | Get instance endpoint (host:port) |
| `pylet logs <id>` | View instance logs |
| `pylet logs <id> --follow` | Follow logs in real-time |
| `pylet cancel <id>` | Cancel instance |
| `pylet list-workers` | List registered workers |

## Key Features

- **Simple**: No containers, no complex configs. Just `pylet start` and `pylet submit`.
- **GPU-aware**: Automatic GPU allocation via `CUDA_VISIBLE_DEVICES`.
- **Service discovery**: Instances get a `PORT` env var; endpoint available via `get-endpoint`.
- **Real-time logs**: Stream logs from running instances.
- **Graceful shutdown**: SIGTERM with configurable grace period before SIGKILL.

## Requirements

- Python 3.9+
- Linux (tested on Ubuntu)

## License

Apache 2.0
