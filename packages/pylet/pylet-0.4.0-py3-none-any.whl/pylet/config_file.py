"""
PyLet Config File - TOML configuration file support.

Design principles:
- One config = one job (no multi-instance files)
- Flat schema (top-level keys, no [instance.name] nesting)
- Strict validation (unknown keys are errors)
- Explicit precedence: CLI > Environment > Config > Defaults
"""

import os
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Version-specific TOML import
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError(
            "Python < 3.11 requires 'tomli' package: pip install tomli"
        )


class ConfigValidationError(Exception):
    """Configuration validation error."""

    pass


# Alias for backwards compatibility
ConfigError = ConfigValidationError


@dataclass
class ResourceConfig:
    """Resource requirements from config file."""

    gpus: Optional[int] = None
    cpus: Optional[int] = None
    memory: Optional[str] = None  # e.g., "16Gi"
    # Advanced fields
    gpu_indices: Optional[List[int]] = None
    exclusive: bool = True
    target_worker: Optional[str] = None


@dataclass
class InstanceConfig:
    """Parsed and validated instance configuration."""

    command: Union[str, List[str]]  # Keep original format
    name: Optional[str] = None
    resources: ResourceConfig = field(default_factory=ResourceConfig)
    env: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)


# Known schema keys for validation
_TOP_LEVEL_KEYS = {"command", "name", "resources", "env", "labels"}
_RESOURCE_KEYS = {"gpus", "cpus", "memory", "gpu_indices", "exclusive", "target_worker"}


def load_config(path: Union[str, Path]) -> dict:
    """Load TOML config file and return raw dict.

    Raises:
        FileNotFoundError: If the config file doesn't exist
        ConfigValidationError: If the TOML syntax is invalid
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    if not path.is_file():
        raise ConfigValidationError(f"Config path is not a file: {path}")

    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigValidationError(f"Invalid TOML syntax in {path}: {e}")


def interpolate_env(value: str) -> str:
    """Replace ${VAR} and $VAR with environment values.

    Variables that don't exist in the environment are left unchanged.
    """

    def replace(match):
        var = match.group(1) or match.group(2)
        return os.environ.get(var, match.group(0))

    return re.sub(r"\$\{(\w+)\}|\$(\w+)", replace, value)


def interpolate_env_values(env_dict: Dict[str, str]) -> Dict[str, str]:
    """Apply environment variable interpolation to all values in a dict."""
    return {key: interpolate_env(value) for key, value in env_dict.items()}


def parse_command(cmd: Union[str, List[str]]) -> str:
    """Convert command config to shell string.

    Supports:
    - Array format: ["python", "train.py", "--epochs", "10"]
    - String format: "python train.py --epochs 10"
    - Multi-line string format
    """
    if isinstance(cmd, list):
        return shlex.join(cmd)
    return cmd.strip()


def _suggest_similar_key(unknown: str, valid_keys: set) -> Optional[str]:
    """Simple typo suggestion."""
    for key in valid_keys:
        # Check for common typos
        if unknown.lower() == key.lower():
            return key
        # Check if it's a prefix/suffix mismatch
        if len(unknown) >= 3 and len(key) >= 3:
            if key.startswith(unknown[:3]) or unknown.startswith(key[:3]):
                return key
        # Check for underscore vs no underscore
        if unknown.replace("_", "") == key.replace("_", ""):
            return key
        if unknown.replace("-", "_") == key:
            return key
    return None


def _validate_type(value: Any, expected_type: type, key: str, path: str) -> None:
    """Validate that a value has the expected type."""
    if not isinstance(value, expected_type):
        actual = type(value).__name__
        expected = expected_type.__name__
        raise ConfigValidationError(
            f"Type error at '{path}': '{key}' should be {expected}, got {actual}"
        )


def validate_config(config: dict) -> InstanceConfig:
    """Validate config dict and return InstanceConfig.

    Raises ConfigValidationError for:
    - Unknown keys (with suggestions for typos)
    - Type mismatches
    - Missing required fields
    - Mutually exclusive fields
    - Invalid values (negative gpus, empty command array)
    """
    # Check for unknown top-level keys
    unknown_top = set(config.keys()) - _TOP_LEVEL_KEYS
    if unknown_top:
        unknown = list(unknown_top)[0]
        suggestion = _suggest_similar_key(unknown, _TOP_LEVEL_KEYS)
        msg = f"Unknown key '{unknown}' in config"
        if suggestion:
            msg += f"\nDid you mean '{suggestion}'?"
        raise ConfigValidationError(msg)

    # Validate required fields
    if "command" not in config:
        raise ConfigValidationError("Missing required field 'command'")

    # Validate command
    cmd = config["command"]
    if not isinstance(cmd, (str, list)):
        raise ConfigValidationError(
            "Type error: 'command' should be string or array, "
            f"got {type(cmd).__name__}"
        )
    if isinstance(cmd, list):
        if len(cmd) == 0:
            raise ConfigValidationError("Command array cannot be empty")
        for i, item in enumerate(cmd):
            if not isinstance(item, str):
                raise ConfigValidationError(
                    f"Type error: command[{i}] should be string, "
                    f"got {type(item).__name__}"
                )
    # Keep command in original format
    command = cmd

    # Validate name
    name = config.get("name")
    if name is not None:
        _validate_type(name, str, "name", "name")

    # Validate resources
    resources = ResourceConfig()
    if "resources" in config:
        res = config["resources"]
        _validate_type(res, dict, "resources", "resources")

        # Check for unknown resource keys
        unknown_res = set(res.keys()) - _RESOURCE_KEYS
        if unknown_res:
            unknown = list(unknown_res)[0]
            suggestion = _suggest_similar_key(unknown, _RESOURCE_KEYS)
            msg = f"Unknown key '{unknown}' in [resources]"
            if suggestion:
                msg += f"\nDid you mean '{suggestion}'?"
            raise ConfigValidationError(msg)

        # Validate each resource field
        if "gpus" in res:
            _validate_type(res["gpus"], int, "gpus", "resources.gpus")
            if res["gpus"] < 0:
                raise ConfigValidationError(
                    "Invalid value: 'gpus' cannot be negative"
                )
            resources.gpus = res["gpus"]

        if "cpus" in res:
            _validate_type(res["cpus"], int, "cpus", "resources.cpus")
            if res["cpus"] < 0:
                raise ConfigValidationError(
                    "Invalid value: 'cpus' cannot be negative"
                )
            resources.cpus = res["cpus"]

        if "memory" in res:
            _validate_type(res["memory"], str, "memory", "resources.memory")
            resources.memory = res["memory"]

        if "gpu_indices" in res:
            indices = res["gpu_indices"]
            if not isinstance(indices, list):
                raise ConfigValidationError(
                    "Type error at 'resources.gpu_indices': "
                    f"should be array, got {type(indices).__name__}"
                )
            for i, idx in enumerate(indices):
                if not isinstance(idx, int):
                    raise ConfigValidationError(
                        f"Type error: gpu_indices[{i}] should be int, "
                        f"got {type(idx).__name__}"
                    )
            resources.gpu_indices = indices

        if "exclusive" in res:
            _validate_type(res["exclusive"], bool, "exclusive", "resources.exclusive")
            resources.exclusive = res["exclusive"]

        if "target_worker" in res:
            _validate_type(
                res["target_worker"], str, "target_worker", "resources.target_worker"
            )
            resources.target_worker = res["target_worker"]

        # Check for mutually exclusive fields
        if (resources.gpus is not None and resources.gpus > 0 and
                resources.gpu_indices is not None):
            raise ConfigValidationError(
                "Mutually exclusive: cannot specify both 'gpus' and 'gpu_indices'. "
                "Use 'gpus' for automatic allocation or 'gpu_indices' for specific GPUs."
            )

    # Validate env (store raw values, interpolation done separately)
    env: Dict[str, str] = {}
    if "env" in config:
        env_dict = config["env"]
        _validate_type(env_dict, dict, "env", "env")
        for key, value in env_dict.items():
            if not isinstance(key, str):
                raise ConfigValidationError(
                    f"Type error: env key should be string, got {type(key).__name__}"
                )
            if not isinstance(value, str):
                raise ConfigValidationError(
                    f"Type error: env['{key}'] should be string, "
                    f"got {type(value).__name__}"
                )
            env[key] = value  # Store raw, don't interpolate here

    # Validate labels
    labels: Dict[str, str] = {}
    if "labels" in config:
        labels_dict = config["labels"]
        _validate_type(labels_dict, dict, "labels", "labels")
        for key, value in labels_dict.items():
            if not isinstance(key, str):
                raise ConfigValidationError(
                    f"Type error: labels key should be string, "
                    f"got {type(key).__name__}"
                )
            if not isinstance(value, str):
                raise ConfigValidationError(
                    f"Type error: labels['{key}'] should be string, "
                    f"got {type(value).__name__}"
                )
            labels[key] = value

    return InstanceConfig(
        command=command,
        name=name,
        resources=resources,
        env=env,
        labels=labels,
    )


def load_and_validate_config(path: Union[str, Path]) -> InstanceConfig:
    """Load and validate a config file in one step.

    If name is not specified in config, defaults to filename without extension.
    """
    path = Path(path)
    raw = load_config(path)
    config = validate_config(raw)

    # Default name to filename without extension
    if config.name is None:
        config.name = path.stem

    return config


# Alias for backwards compatibility
load_and_validate = load_and_validate_config


def apply_precedence(
    config: InstanceConfig,
    cli_args: Dict[str, Any],
    defaults: Optional[Dict[str, Any]] = None,
) -> InstanceConfig:
    """Apply precedence: CLI > Config > Defaults.

    Args:
        config: Base config from file
        cli_args: CLI argument overrides (None values are ignored)
        defaults: Default values to use if not in config or CLI

    Returns:
        New InstanceConfig with precedence applied
    """
    defaults = defaults or {}

    # Start with config values
    name = config.name
    command = config.command
    gpus = config.resources.gpus
    cpus = config.resources.cpus
    memory = config.resources.memory
    gpu_indices = config.resources.gpu_indices
    exclusive = config.resources.exclusive
    target_worker = config.resources.target_worker
    env = dict(config.env)
    labels = dict(config.labels)

    # Apply defaults for None values
    if gpus is None:
        gpus = defaults.get("gpus")
    if cpus is None:
        cpus = defaults.get("cpus")
    if memory is None:
        memory = defaults.get("memory")

    # Apply CLI overrides (None means not specified)
    if cli_args.get("name") is not None:
        name = cli_args["name"]
    if cli_args.get("command") is not None:
        command = cli_args["command"]
    if cli_args.get("gpus") is not None:
        gpus = cli_args["gpus"]
    if cli_args.get("cpus") is not None:
        cpus = cli_args["cpus"]
    if cli_args.get("memory") is not None:
        memory = cli_args["memory"]
    if cli_args.get("gpu_indices") is not None:
        gpu_indices = cli_args["gpu_indices"]
    if cli_args.get("exclusive") is not None:
        exclusive = cli_args["exclusive"]
    if cli_args.get("target_worker") is not None:
        target_worker = cli_args["target_worker"]

    return InstanceConfig(
        name=name,
        command=command,
        resources=ResourceConfig(
            gpus=gpus,
            cpus=cpus,
            memory=memory,
            gpu_indices=gpu_indices,
            exclusive=exclusive,
            target_worker=target_worker,
        ),
        env=env,
        labels=labels,
    )


def parse_memory(memory_str: str) -> int:
    """Parse memory string like '16Gi' or '1024Mi' to MB.

    Supports:
    - Gi/G: Gibibytes (1024 MB)
    - Mi/M: Mebibytes
    - Ki/K: Kibibytes (1/1024 MB)
    - Plain numbers: assumed to be MB
    """
    if not memory_str:
        return 0

    memory_str = memory_str.strip()

    # Match number and optional unit
    match = re.match(r"^(\d+(?:\.\d+)?)\s*([a-zA-Z]*)$", memory_str)
    if not match:
        raise ConfigValidationError(f"Invalid memory format: '{memory_str}'")

    value = float(match.group(1))
    unit = match.group(2).lower()

    if unit in ("gi", "g"):
        return int(value * 1024)
    elif unit in ("mi", "m", ""):
        return int(value)
    elif unit in ("ki", "k"):
        return max(1, int(value / 1024))
    elif unit in ("ti", "t"):
        return int(value * 1024 * 1024)
    else:
        raise ConfigValidationError(f"Unknown memory unit: '{unit}' in '{memory_str}'")
