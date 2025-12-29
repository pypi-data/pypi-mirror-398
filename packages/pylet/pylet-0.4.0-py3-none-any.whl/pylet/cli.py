"""
PyLet CLI - Command-line interface for the PyLet cluster.
"""

import asyncio
from pathlib import Path
from typing import Optional

import click
import uvicorn

from pylet.client import PyletClient
from pylet.config_file import ConfigValidationError, load_and_validate_config, parse_command, parse_memory
from pylet.logger import configure_file_logging
from pylet.server import app
from pylet.worker import Worker


@click.group()
def cli():
    """PyLet - Distributed instance execution system."""
    pass


@cli.command()
@click.option(
    "--head",
    type=str,
    default=None,
    help="Head node address (ip:port). If not provided, starts the head node.",
)
@click.option(
    "--cpu-cores",
    type=int,
    default=4,
    help="Number of CPU cores for the worker.",
)
@click.option(
    "--gpu-units",
    type=int,
    default=0,
    help="Number of GPU units for the worker.",
)
@click.option(
    "--memory-mb",
    type=int,
    default=4096,
    help="Amount of memory in MB for the worker.",
)
def start(head, cpu_cores, gpu_units, memory_mb):
    """Start the PyLet server (head node) or a worker node."""
    # Configure file logging for server/worker processes
    configure_file_logging()

    if head is None:
        # Start the server (head node)
        click.echo("Starting PyLet server...")
        uvicorn.run(
            "pylet.server:app", host="0.0.0.0", port=8000, reload=False
        )
    else:
        # Start a worker node connected to the head node
        click.echo(f"Starting PyLet worker connected to head node at {head}...")
        worker = Worker(
            head_address=head,
            cpu_cores=cpu_cores,
            gpu_units=gpu_units,
            memory_mb=memory_mb,
        )
        asyncio.run(worker.run())


@cli.command()
@click.argument("command", nargs=-1, required=False)
@click.option("--config", "-c", type=click.Path(exists=True), help="TOML config file.")
@click.option("--cpu-cores", type=int, default=None, help="CPU cores required.")
@click.option("--gpu-units", type=int, default=None, help="GPU units required.")
@click.option("--memory-mb", type=int, default=None, help="Memory in MB required.")
@click.option("--name", type=str, default=None, help="Optional instance name.")
# SLLM support options
@click.option("--target-worker", default=None, help="Target worker node.")
@click.option("--gpu-indices", default=None, help="Specific GPU indices (comma-separated).")
@click.option("--exclusive/--no-exclusive", default=True, help="GPU exclusivity mode.")
@click.option("--label", multiple=True, help="Labels (key=value).")
@click.option("--env", "env_vars", multiple=True, help="Env vars (key=value).")
# Venv support
@click.option("--venv", default=None, help="Path to pre-existing virtualenv (must be absolute).")
def submit(command, config, cpu_cores, gpu_units, memory_mb, name,
           target_worker, gpu_indices, exclusive, label, env_vars, venv):
    """Submit a new instance to the PyLet cluster.

    Precedence (highest wins): CLI args > Config file > Defaults

    Examples:

        # Simple command
        pylet submit python train.py --epochs 10

        # Using config file
        pylet submit --config job.toml

        # Config file with CLI override
        pylet submit --config job.toml --gpu-units 0

        # SLLM examples
        pylet submit "vllm serve model" --target-worker gpu-0 --gpu-indices 0,1

        pylet submit "sllm-store start" --target-worker gpu-0 --gpu-indices 0,1,2,3 --no-exclusive
    """
    # Resolve values with precedence: CLI > Config > Defaults
    final_command: Optional[str] = None
    final_name: Optional[str] = name
    final_cpu_cores: int = 1  # default
    final_gpu_units: int = 0  # default
    final_memory_mb: int = 512  # default

    # Load config if provided
    if config:
        try:
            cfg = load_and_validate_config(config)

            # Apply config values (can be overridden by CLI)
            # parse_command converts array to shell string if needed
            final_command = parse_command(cfg.command)
            if cfg.name:
                final_name = cfg.name

            # Map config resources to CLI format
            # Note: config uses 'gpus', CLI uses 'gpu_units'
            if cfg.resources.cpus is not None:
                final_cpu_cores = cfg.resources.cpus
            if cfg.resources.gpus is not None:
                final_gpu_units = cfg.resources.gpus
            if cfg.resources.memory:
                final_memory_mb = parse_memory(cfg.resources.memory)

        except ConfigValidationError as e:
            click.echo(f"Config error: {e}", err=True)
            raise SystemExit(1)

    # Apply CLI overrides (highest precedence)
    if command:
        final_command = " ".join(command)
    if cpu_cores is not None:
        final_cpu_cores = cpu_cores
    if gpu_units is not None:
        final_gpu_units = gpu_units
    if memory_mb is not None:
        final_memory_mb = memory_mb
    if name is not None:
        final_name = name

    # Validate that we have a command
    if not final_command:
        click.echo("Error: command is required (via argument or --config)", err=True)
        raise SystemExit(1)

    # Parse gpu_indices
    parsed_gpu_indices = None
    if gpu_indices:
        parsed_gpu_indices = [int(x.strip()) for x in gpu_indices.split(",")]

    # Parse labels
    labels = {}
    for lbl in label:
        if "=" not in lbl:
            click.echo(f"Invalid label format: {lbl}. Expected key=value", err=True)
            raise SystemExit(1)
        key, value = lbl.split("=", 1)
        labels[key] = value

    # Parse env vars
    env = {}
    for e in env_vars:
        if "=" not in e:
            click.echo(f"Invalid env format: {e}. Expected key=value", err=True)
            raise SystemExit(1)
        key, value = e.split("=", 1)
        env[key] = value

    async def submit_instance():
        client = PyletClient()
        try:
            instance_id = await client.submit_instance(
                command=final_command,
                resource_requirements={
                    "cpu_cores": final_cpu_cores,
                    "gpu_units": final_gpu_units,
                    "memory_mb": final_memory_mb,
                },
                name=final_name,
                target_worker=target_worker,
                gpu_indices=parsed_gpu_indices,
                exclusive=exclusive,
                labels=labels if labels else None,
                env=env if env else None,
                venv=venv,
            )
            click.echo(f"Instance submitted with ID: {instance_id}")
        except Exception as e:
            click.echo(f"Error submitting instance: {e}", err=True)
        finally:
            await client.close()

    asyncio.run(submit_instance())


@cli.command("get-instance")
@click.option("--instance-id", type=str, help="Instance ID.")
@click.option("--name", type=str, help="Instance name.")
def get_instance(instance_id, name):
    """Get instance details by ID or name."""

    async def get_instance_details():
        client = PyletClient()
        try:
            if name:
                instance = await client.get_instance_by_name(name)
            elif instance_id:
                instance = await client.get_instance(instance_id)
            else:
                click.echo("Error: must provide --instance-id or --name", err=True)
                return
            click.echo(f"Instance details: {instance}")
        except Exception as e:
            click.echo(f"Error retrieving instance: {e}", err=True)
        finally:
            await client.close()

    asyncio.run(get_instance_details())


@cli.command("get-result")
@click.argument("instance_id", type=str)
def get_result(instance_id):
    """Get the result of an instance by ID."""

    async def get_instance_result():
        client = PyletClient()
        try:
            result = await client.get_instance_result(instance_id)
            click.echo(f"Instance result: {result}")
        except Exception as e:
            click.echo(f"Error retrieving instance result: {e}", err=True)
        finally:
            await client.close()

    asyncio.run(get_instance_result())


@cli.command("list-workers")
def list_workers():
    """List all registered workers."""

    async def list_all_workers():
        client = PyletClient()
        try:
            workers = await client.list_workers()
            if not workers:
                click.echo("No workers registered.")
            else:
                for w in workers:
                    status = w.get("status", "UNKNOWN")
                    click.echo(
                        f"Worker {w['worker_id']} ({w['host']}) - {status} - "
                        f"GPUs: {w['total_resources']['gpu_units']}"
                    )
        except Exception as e:
            click.echo(f"Error listing workers: {e}", err=True)
        finally:
            await client.close()

    asyncio.run(list_all_workers())


@cli.command("get-endpoint")
@click.option("--instance-id", type=str, help="Instance ID.")
@click.option("--name", type=str, help="Instance name.")
def get_endpoint(instance_id, name):
    """Get the endpoint (host:port) of a running instance."""

    async def get_instance_endpoint():
        client = PyletClient()
        try:
            if name:
                endpoint = await client.get_instance_endpoint_by_name(name)
            elif instance_id:
                endpoint = await client.get_instance_endpoint(instance_id)
            else:
                click.echo("Error: must provide --instance-id or --name", err=True)
                return
            click.echo(endpoint)
        except Exception as e:
            click.echo(f"Error retrieving endpoint: {e}", err=True)
        finally:
            await client.close()

    asyncio.run(get_instance_endpoint())


@cli.command()
@click.argument("instance_id", type=str)
def cancel(instance_id):
    """Cancel a running instance."""

    async def cancel_instance():
        client = PyletClient()
        try:
            result = await client.cancel_instance(instance_id)
            status = result.get("status", "unknown")
            if status == "cancelling":
                click.echo(f"Cancellation requested for instance {instance_id}")
            elif status == "already_cancelling":
                click.echo(f"Instance {instance_id} is already being cancelled")
            else:
                click.echo(f"Cancel result: {result}")
        except Exception as e:
            click.echo(f"Error cancelling instance: {e}", err=True)
        finally:
            await client.close()

    asyncio.run(cancel_instance())


@cli.command()
@click.argument("instance_id", type=str)
@click.option("--tail", type=int, default=None, help="Get last N bytes only.")
@click.option("--follow", "-f", is_flag=True, help="Follow log output (poll for new content).")
def logs(instance_id, tail, follow):
    """Get logs from an instance."""
    import sys
    import time

    async def get_logs():
        client = PyletClient()
        try:
            # Get initial log info
            result = await client.get_logs(instance_id, offset=0, limit=0)
            total_size = result.get("total_size", 0)
            available_offset = result.get("available_offset", 0)

            # Calculate starting offset
            if tail is not None:
                offset = max(available_offset, total_size - tail)
            else:
                offset = available_offset

            # Fetch and print logs
            while True:
                result = await client.get_logs(
                    instance_id,
                    offset=offset,
                    limit=10 * 1024 * 1024,  # 10MB chunks
                )

                data = result.get("data", b"")
                if data:
                    # Write to stdout as bytes
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
                    offset += len(data)

                if not follow:
                    break

                # Check if instance is still running
                instance = await client.get_instance(instance_id)
                status = instance.get("status", "")
                if status in ("COMPLETED", "FAILED", "CANCELLED"):
                    # One more fetch to get any remaining logs
                    final_result = await client.get_logs(
                        instance_id,
                        offset=offset,
                        limit=10 * 1024 * 1024,
                    )
                    final_data = final_result.get("data", b"")
                    if final_data:
                        sys.stdout.buffer.write(final_data)
                        sys.stdout.buffer.flush()
                    break

                # Poll interval
                await asyncio.sleep(1.0)

        except Exception as e:
            click.echo(f"Error retrieving logs: {e}", err=True)
        finally:
            await client.close()

    asyncio.run(get_logs())


if __name__ == "__main__":
    cli()
