"""
PyLet Worker HTTP Server - Serves instance logs and future metrics.

Exposes:
- GET /logs/{instance_id}?offset=0&limit=1048576
- GET /health (future)
- GET /metrics (future)

Uses global byte offset semantics - client provides logical offset across
all rotated log files, server handles file boundary math.
"""

import asyncio
import base64
from pathlib import Path
from typing import List, Tuple

from aiohttp import web

from pylet import config
from pylet.logger import logger


def get_log_files(instance_id: str) -> List[Tuple[int, Path]]:
    """
    Get sorted list of (index, path) tuples for an instance's log files.
    Returns empty list if no files exist.
    """
    log_dir = config.LOG_DIR
    base_pattern = f"{instance_id}."

    files = []
    if not log_dir.exists():
        return files

    for f in log_dir.iterdir():
        if f.name.startswith(base_pattern):
            try:
                idx = int(f.name[len(base_pattern):])
                files.append((idx, f))
            except ValueError:
                pass

    # Sort by index (oldest first)
    files.sort(key=lambda x: x[0])
    return files


def calculate_file_ranges(files: List[Tuple[int, Path]]) -> List[Tuple[int, int, Path]]:
    """
    Calculate (start_offset, end_offset, path) for each file.
    Returns list of tuples sorted by offset.
    """
    ranges = []
    current_offset = 0

    for idx, path in files:
        size = path.stat().st_size
        ranges.append((current_offset, current_offset + size, path))
        current_offset += size

    return ranges


def read_bytes_from_files(
    ranges: List[Tuple[int, int, Path]],
    offset: int,
    limit: int,
) -> bytes:
    """
    Read bytes from the given offset with the given limit.
    Handles reading across file boundaries.
    """
    if not ranges:
        return b""

    result = bytearray()
    bytes_remaining = limit

    for start_off, end_off, path in ranges:
        # Skip files before our offset
        if end_off <= offset:
            continue

        # Stop if we've read enough
        if bytes_remaining <= 0:
            break

        # Calculate how much to read from this file
        file_offset = max(0, offset - start_off)
        file_size = end_off - start_off
        bytes_to_read = min(file_size - file_offset, bytes_remaining)

        if bytes_to_read <= 0:
            continue

        with open(path, "rb") as f:
            f.seek(file_offset)
            data = f.read(bytes_to_read)
            result.extend(data)
            bytes_remaining -= len(data)

    return bytes(result)


async def handle_logs(request: web.Request) -> web.Response:
    """Handle GET /logs/{instance_id}"""
    instance_id = request.match_info["instance_id"]

    # Parse query params
    offset = int(request.query.get("offset", 0))
    limit = int(request.query.get("limit", config.LOG_MAX_RESPONSE_SIZE))

    # Cap limit to max response size
    limit = min(limit, config.LOG_MAX_RESPONSE_SIZE)

    # Get log files for this instance
    files = get_log_files(instance_id)

    if not files:
        # No log files yet - return empty response
        return web.json_response({
            "available_offset": 0,
            "total_size": 0,
            "content": "",
            "size": 0,
        })

    # Calculate file ranges
    ranges = calculate_file_ranges(files)
    total_size = ranges[-1][1] if ranges else 0
    available_offset = ranges[0][0] if ranges else 0

    # Clamp offset to available range
    if offset < available_offset:
        offset = available_offset
    if offset > total_size:
        offset = total_size

    # Read the bytes
    data = read_bytes_from_files(ranges, offset, limit)

    # Base64 encode for JSON transport
    content_b64 = base64.b64encode(data).decode("ascii")

    return web.json_response({
        "available_offset": available_offset,
        "total_size": total_size,
        "content": content_b64,
        "size": len(data),
    })


async def handle_health(request: web.Request) -> web.Response:
    """Handle GET /health"""
    return web.json_response({"status": "ok"})


def create_app() -> web.Application:
    """Create the aiohttp web application."""
    app = web.Application()
    app.router.add_get("/logs/{instance_id}", handle_logs)
    app.router.add_get("/health", handle_health)
    return app


async def run_server(port: int = None) -> None:
    """Run the worker HTTP server."""
    port = port or config.WORKER_HTTP_PORT
    app = create_app()

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"Worker HTTP server started on port {port}")

    # Run forever
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(run_server())
