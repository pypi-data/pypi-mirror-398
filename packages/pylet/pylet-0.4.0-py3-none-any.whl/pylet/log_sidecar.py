"""
PyLet Log Sidecar - Captures stdin and writes to rotating log files.

Usage:
    python3 -m pylet.log_sidecar <log_dir> <instance_id>

Reads stdin, writes to log files with rotation. Designed to be used as a
pipe target for capturing instance stdout/stderr.

Log files are named: {instance_id}.{index}
- Index increases over time (no renames on rotation)
- On rotation: create new file, delete oldest if > MAX_FILES
"""

import sys
from pathlib import Path


# Read from config at import time
try:
    from pylet.config import LOG_CHUNK_SIZE, LOG_MAX_FILES
except ImportError:
    # Fallback defaults if config not available
    LOG_CHUNK_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_MAX_FILES = 5

# Read chunk size from stdin
READ_CHUNK_SIZE = 64 * 1024  # 64KB


def main() -> int:
    """Main entry point for log sidecar."""
    if len(sys.argv) != 3:
        sys.stderr.write(
            f"Usage: {sys.argv[0]} <log_dir> <instance_id>\n"
        )
        return 1

    log_dir = Path(sys.argv[1])
    instance_id = sys.argv[2]

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    # Find existing log files to determine starting index
    base_pattern = f"{instance_id}."
    existing_indices = []
    for f in log_dir.iterdir():
        if f.name.startswith(base_pattern):
            try:
                idx = int(f.name[len(base_pattern):])
                existing_indices.append(idx)
            except ValueError:
                pass

    # Start from next index (or 1 if no files exist)
    current_idx = max(existing_indices, default=0) + 1
    current_path = log_dir / f"{base_pattern}{current_idx}"
    current_file = open(current_path, "wb")
    current_size = 0

    try:
        while True:
            # Use read1() to read whatever is immediately available (non-blocking)
            # read() blocks until READ_CHUNK_SIZE bytes or EOF - that's wrong for streaming
            chunk = sys.stdin.buffer.read1(READ_CHUNK_SIZE)
            if not chunk:
                break  # EOF

            # Check if rotation needed before writing
            if current_size + len(chunk) > LOG_CHUNK_SIZE:
                current_file.close()

                # Delete oldest file if we have too many
                all_indices = sorted(existing_indices + [current_idx])
                while len(all_indices) >= LOG_MAX_FILES:
                    oldest_idx = all_indices.pop(0)
                    oldest_path = log_dir / f"{base_pattern}{oldest_idx}"
                    try:
                        oldest_path.unlink()
                    except FileNotFoundError:
                        pass

                # Open new file
                current_idx += 1
                existing_indices.append(current_idx - 1)  # Previous file now exists
                current_path = log_dir / f"{base_pattern}{current_idx}"
                current_file = open(current_path, "wb")
                current_size = 0

            # Write chunk
            current_file.write(chunk)
            current_file.flush()
            current_size += len(chunk)

    except BrokenPipeError:
        # Reader closed, exit cleanly
        pass
    finally:
        current_file.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
