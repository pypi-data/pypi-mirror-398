"""Unit tests for pylet.config_file module (TDD - tests written before implementation).

This module tests TOML config file loading for PyLet instance definitions.
"""

import os
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest.mock import patch


# =============================================================================
# Test: TOML Loading
# =============================================================================


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_toml_file(self, tmp_path):
        """Test loading a valid TOML config file."""
        from pylet.config_file import load_config

        config_file = tmp_path / "job.toml"
        config_file.write_text("""
name = "test-job"
command = "echo hello"

[resources]
gpus = 1
""")
        config = load_config(str(config_file))
        assert config["name"] == "test-job"
        assert config["command"] == "echo hello"
        assert config["resources"]["gpus"] == 1

    def test_load_nonexistent_file_raises(self, tmp_path):
        """Test that loading a nonexistent file raises FileNotFoundError."""
        from pylet.config_file import load_config

        with pytest.raises(FileNotFoundError):
            load_config(str(tmp_path / "nonexistent.toml"))

    def test_load_invalid_toml_raises(self, tmp_path):
        """Test that invalid TOML syntax raises an error."""
        from pylet.config_file import load_config

        config_file = tmp_path / "invalid.toml"
        config_file.write_text("""
name = "unclosed string
""")
        # tomllib raises TOMLDecodeError
        with pytest.raises(Exception):  # TOMLDecodeError
            load_config(str(config_file))

    def test_load_empty_file(self, tmp_path):
        """Test loading an empty TOML file."""
        from pylet.config_file import load_config

        config_file = tmp_path / "empty.toml"
        config_file.write_text("")
        config = load_config(str(config_file))
        assert config == {}

    def test_load_with_comments(self, tmp_path):
        """Test that TOML comments are ignored."""
        from pylet.config_file import load_config

        config_file = tmp_path / "commented.toml"
        config_file.write_text("""
# This is a comment
name = "test"  # inline comment
# gpus = 999  # commented out
""")
        config = load_config(str(config_file))
        assert config["name"] == "test"
        assert "gpus" not in config


# =============================================================================
# Test: Config Validation (Strict)
# =============================================================================


class TestValidateConfig:
    """Tests for validate_config function - strict validation."""

    def test_valid_minimal_config(self):
        """Test validation of minimal valid config (just command)."""
        from pylet.config_file import validate_config, InstanceConfig

        config = {"command": "echo hello"}
        result = validate_config(config)
        assert isinstance(result, InstanceConfig)
        assert result.command == "echo hello"

    def test_valid_full_config(self):
        """Test validation of full config with all fields."""
        from pylet.config_file import validate_config

        config = {
            "name": "my-job",
            "command": ["python", "train.py"],
            "resources": {
                "gpus": 2,
                "cpus": 8,
                "memory": "32Gi",
            },
            "env": {
                "HF_TOKEN": "${HF_TOKEN}",
            },
            "labels": {
                "type": "training",
            },
        }
        result = validate_config(config)
        assert result.name == "my-job"
        assert result.command == ["python", "train.py"]
        assert result.resources.gpus == 2
        assert result.resources.cpus == 8
        assert result.resources.memory == "32Gi"
        assert result.env == {"HF_TOKEN": "${HF_TOKEN}"}
        assert result.labels == {"type": "training"}

    def test_missing_command_raises(self):
        """Test that missing 'command' field raises error."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {"name": "no-command"}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "command" in str(exc_info.value).lower()

    def test_unknown_key_raises(self):
        """Test that unknown top-level key raises error."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {
            "command": "echo hello",
            "unknown_key": "value",
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "unknown_key" in str(exc_info.value).lower()

    def test_unknown_resource_key_raises(self):
        """Test that unknown key in [resources] raises error."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {
            "command": "echo hello",
            "resources": {
                "gpus": 1,
                "memory_limit": "16Gi",  # typo: should be "memory"
            },
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "memory_limit" in str(exc_info.value).lower()

    def test_type_error_gpus_string(self):
        """Test that string gpus value raises type error."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {
            "command": "echo hello",
            "resources": {
                "gpus": "1",  # should be int
            },
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "gpus" in str(exc_info.value).lower()
        assert "int" in str(exc_info.value).lower() or "type" in str(exc_info.value).lower()

    def test_type_error_command_int(self):
        """Test that integer command raises type error."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {"command": 123}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "command" in str(exc_info.value).lower()

    def test_mutual_exclusion_gpus_and_gpu_indices(self):
        """Test that both gpus and gpu_indices raises error."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {
            "command": "echo hello",
            "resources": {
                "gpus": 2,
                "gpu_indices": [0, 1],
            },
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        error_msg = str(exc_info.value).lower()
        assert "gpus" in error_msg
        assert "gpu_indices" in error_msg
        assert "mutually exclusive" in error_msg or "exclusive" in error_msg

    def test_gpu_indices_valid(self):
        """Test valid gpu_indices configuration."""
        from pylet.config_file import validate_config

        config = {
            "command": "echo hello",
            "resources": {
                "gpu_indices": [0, 1, 2],
            },
        }
        result = validate_config(config)
        assert result.resources.gpu_indices == [0, 1, 2]

    def test_exclusive_default_true(self):
        """Test that exclusive defaults to True."""
        from pylet.config_file import validate_config

        config = {
            "command": "echo hello",
            "resources": {"gpus": 1},
        }
        result = validate_config(config)
        assert result.resources.exclusive is True

    def test_exclusive_can_be_false(self):
        """Test that exclusive can be set to False."""
        from pylet.config_file import validate_config

        config = {
            "command": "echo hello",
            "resources": {
                "gpu_indices": [0, 1],
                "exclusive": False,
            },
        }
        result = validate_config(config)
        assert result.resources.exclusive is False

    def test_target_worker_valid(self):
        """Test valid target_worker configuration."""
        from pylet.config_file import validate_config

        config = {
            "command": "echo hello",
            "resources": {
                "target_worker": "gpu-node-0",
            },
        }
        result = validate_config(config)
        assert result.resources.target_worker == "gpu-node-0"

    def test_env_must_be_dict(self):
        """Test that [env] must be a dict."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {
            "command": "echo hello",
            "env": "not a dict",
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "env" in str(exc_info.value).lower()

    def test_labels_must_be_dict(self):
        """Test that [labels] must be a dict."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {
            "command": "echo hello",
            "labels": ["not", "a", "dict"],
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "labels" in str(exc_info.value).lower()

    def test_env_values_must_be_strings(self):
        """Test that env values must be strings."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {
            "command": "echo hello",
            "env": {
                "SOME_VAR": 123,  # should be string
            },
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "env" in str(exc_info.value).lower()

    def test_labels_values_must_be_strings(self):
        """Test that label values must be strings."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {
            "command": "echo hello",
            "labels": {
                "count": 123,  # should be string
            },
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "labels" in str(exc_info.value).lower()


# =============================================================================
# Test: InstanceConfig Dataclass
# =============================================================================


class TestInstanceConfig:
    """Tests for InstanceConfig dataclass."""

    def test_instance_config_attributes(self):
        """Test InstanceConfig has all expected attributes."""
        from pylet.config_file import InstanceConfig, ResourceConfig

        config = InstanceConfig(
            name="test",
            command="echo hello",
            resources=ResourceConfig(),
            env={},
            labels={},
        )
        assert hasattr(config, "name")
        assert hasattr(config, "command")
        assert hasattr(config, "resources")
        assert hasattr(config, "env")
        assert hasattr(config, "labels")

    def test_resource_config_defaults(self):
        """Test ResourceConfig has sensible defaults."""
        from pylet.config_file import ResourceConfig

        rc = ResourceConfig()
        assert rc.gpus is None
        assert rc.cpus is None
        assert rc.memory is None
        assert rc.gpu_indices is None
        assert rc.exclusive is True
        assert rc.target_worker is None


# =============================================================================
# Test: Command Parsing
# =============================================================================


class TestParseCommand:
    """Tests for parse_command function."""

    def test_parse_string_command(self):
        """Test parsing a simple string command."""
        from pylet.config_file import parse_command

        result = parse_command("echo hello world")
        assert result == "echo hello world"

    def test_parse_array_command(self):
        """Test parsing an array command into shell string."""
        from pylet.config_file import parse_command

        result = parse_command(["python", "train.py", "--epochs", "10"])
        assert result == "python train.py --epochs 10"

    def test_parse_array_with_spaces(self):
        """Test array command with arguments containing spaces."""
        from pylet.config_file import parse_command

        result = parse_command(["python", "main.py", "--prompt", "Hello World"])
        # shlex.join should quote the argument with spaces
        assert "Hello World" in result or "'Hello World'" in result or '"Hello World"' in result

    def test_parse_multiline_string(self):
        """Test parsing multiline string command."""
        from pylet.config_file import parse_command

        cmd = """vllm serve model \\
  --port 8080 \\
  --host 0.0.0.0"""
        result = parse_command(cmd)
        assert "vllm serve model" in result

    def test_parse_string_strips_whitespace(self):
        """Test that string command is stripped of leading/trailing whitespace."""
        from pylet.config_file import parse_command

        result = parse_command("  echo hello  \n")
        assert result == "echo hello"

    def test_parse_array_with_special_chars(self):
        """Test array command with special shell characters."""
        from pylet.config_file import parse_command

        result = parse_command(["echo", "$HOME", "&&", "ls"])
        # Result should be properly escaped for shell
        assert "echo" in result


# =============================================================================
# Test: Environment Variable Interpolation
# =============================================================================


class TestInterpolateEnv:
    """Tests for interpolate_env function."""

    def test_interpolate_dollar_brace_syntax(self):
        """Test ${VAR} syntax interpolation."""
        from pylet.config_file import interpolate_env

        with patch.dict(os.environ, {"MY_VAR": "my_value"}):
            result = interpolate_env("prefix_${MY_VAR}_suffix")
            assert result == "prefix_my_value_suffix"

    def test_interpolate_dollar_syntax(self):
        """Test $VAR syntax interpolation."""
        from pylet.config_file import interpolate_env

        with patch.dict(os.environ, {"MY_VAR": "my_value"}):
            result = interpolate_env("prefix_$MY_VAR_suffix")
            # Note: $MY_VAR_suffix might be interpreted as one variable
            # depending on implementation. Let's test simpler case:
            result = interpolate_env("$MY_VAR")
            assert result == "my_value"

    def test_interpolate_missing_var_unchanged(self):
        """Test that missing env var leaves placeholder unchanged."""
        from pylet.config_file import interpolate_env

        # Ensure var doesn't exist
        env_copy = os.environ.copy()
        if "NONEXISTENT_VAR_12345" in env_copy:
            del env_copy["NONEXISTENT_VAR_12345"]

        with patch.dict(os.environ, env_copy, clear=True):
            result = interpolate_env("${NONEXISTENT_VAR_12345}")
            assert result == "${NONEXISTENT_VAR_12345}"

    def test_interpolate_multiple_vars(self):
        """Test interpolating multiple variables."""
        from pylet.config_file import interpolate_env

        with patch.dict(os.environ, {"VAR1": "one", "VAR2": "two"}):
            result = interpolate_env("${VAR1} and ${VAR2}")
            assert result == "one and two"

    def test_interpolate_empty_string(self):
        """Test interpolating empty string."""
        from pylet.config_file import interpolate_env

        result = interpolate_env("")
        assert result == ""

    def test_interpolate_no_vars(self):
        """Test string with no variables."""
        from pylet.config_file import interpolate_env

        result = interpolate_env("plain text")
        assert result == "plain text"

    def test_interpolate_env_in_config(self):
        """Test env interpolation applied to config env values."""
        from pylet.config_file import validate_config, interpolate_env_values

        config = {
            "command": "echo hello",
            "env": {
                "TOKEN": "${MY_TOKEN}",
                "STATIC": "fixed_value",
            },
        }
        with patch.dict(os.environ, {"MY_TOKEN": "secret123"}):
            result = validate_config(config)
            interpolated = interpolate_env_values(result.env)
            assert interpolated["TOKEN"] == "secret123"
            assert interpolated["STATIC"] == "fixed_value"


# =============================================================================
# Test: Precedence Handling
# =============================================================================


class TestApplyPrecedence:
    """Tests for apply_precedence function - CLI > Env > Config > Defaults."""

    def test_config_values_used_as_base(self):
        """Test that config values are used when no overrides."""
        from pylet.config_file import apply_precedence, InstanceConfig, ResourceConfig

        config = InstanceConfig(
            name="config-name",
            command="config-cmd",
            resources=ResourceConfig(gpus=2),
            env={},
            labels={},
        )
        result = apply_precedence(config, cli_args={})
        assert result.name == "config-name"
        assert result.resources.gpus == 2

    def test_cli_overrides_config(self):
        """Test that CLI args override config values."""
        from pylet.config_file import apply_precedence, InstanceConfig, ResourceConfig

        config = InstanceConfig(
            name="config-name",
            command="config-cmd",
            resources=ResourceConfig(gpus=2),
            env={},
            labels={},
        )
        cli_args = {"gpus": 0, "name": "cli-name"}
        result = apply_precedence(config, cli_args=cli_args)
        assert result.name == "cli-name"
        assert result.resources.gpus == 0

    def test_cli_none_does_not_override(self):
        """Test that CLI args with None value don't override config."""
        from pylet.config_file import apply_precedence, InstanceConfig, ResourceConfig

        config = InstanceConfig(
            name="config-name",
            command="config-cmd",
            resources=ResourceConfig(gpus=2),
            env={},
            labels={},
        )
        cli_args = {"gpus": None, "name": None}
        result = apply_precedence(config, cli_args=cli_args)
        assert result.name == "config-name"
        assert result.resources.gpus == 2

    def test_defaults_used_when_not_specified(self):
        """Test that defaults are used when neither CLI nor config specifies."""
        from pylet.config_file import apply_precedence, InstanceConfig, ResourceConfig

        config = InstanceConfig(
            name=None,  # not specified
            command="cmd",
            resources=ResourceConfig(),  # gpus=None
            env={},
            labels={},
        )
        result = apply_precedence(config, cli_args={}, defaults={"gpus": 0})
        assert result.resources.gpus == 0

    def test_config_name_defaults_to_filename(self, tmp_path):
        """Test that name defaults to filename without extension."""
        from pylet.config_file import load_and_validate_config

        config_file = tmp_path / "my-inference-job.toml"
        config_file.write_text('command = "echo hello"')

        result = load_and_validate_config(str(config_file))
        assert result.name == "my-inference-job"

    def test_explicit_name_overrides_filename(self, tmp_path):
        """Test that explicit name in config overrides filename default."""
        from pylet.config_file import load_and_validate_config

        config_file = tmp_path / "filename.toml"
        config_file.write_text('''
name = "explicit-name"
command = "echo hello"
''')
        result = load_and_validate_config(str(config_file))
        assert result.name == "explicit-name"


# =============================================================================
# Test: Full Integration (Load + Validate + Parse)
# =============================================================================


class TestFullConfigWorkflow:
    """Integration tests for complete config workflow."""

    def test_load_validate_inference_config(self, tmp_path):
        """Test loading and validating a realistic inference config."""
        from pylet.config_file import load_and_validate_config

        config_file = tmp_path / "inference.toml"
        config_file.write_text('''
# inference.toml
name = "vllm-inference"
command = [
    "vllm", "serve", "Qwen/Qwen2.5-1.5B-Instruct",
    "--port", "$PORT",
    "--host", "0.0.0.0",
]

[resources]
gpus = 1
cpus = 4
memory = "16Gi"

[env]
HF_TOKEN = "${HF_TOKEN}"
MODEL_REVISION = "main"

[labels]
type = "inference"
model = "qwen-2.5"
''')
        result = load_and_validate_config(str(config_file))
        assert result.name == "vllm-inference"
        assert result.command == [
            "vllm", "serve", "Qwen/Qwen2.5-1.5B-Instruct",
            "--port", "$PORT",
            "--host", "0.0.0.0",
        ]
        assert result.resources.gpus == 1
        assert result.resources.cpus == 4
        assert result.resources.memory == "16Gi"
        assert result.env["HF_TOKEN"] == "${HF_TOKEN}"
        assert result.labels["type"] == "inference"

    def test_load_validate_training_config(self, tmp_path):
        """Test loading and validating a training config."""
        from pylet.config_file import load_and_validate_config

        config_file = tmp_path / "training.toml"
        config_file.write_text('''
name = "llama-finetune"
command = [
    "python", "train.py",
    "--model", "meta-llama/Llama-2-7b",
    "--epochs", "10",
]

[resources]
gpus = 2
cpus = 8
memory = "32Gi"

[env]
WANDB_API_KEY = "${WANDB_API_KEY}"

[labels]
type = "training"
''')
        result = load_and_validate_config(str(config_file))
        assert result.name == "llama-finetune"
        assert result.resources.gpus == 2

    def test_load_validate_sllm_advanced_config(self, tmp_path):
        """Test loading advanced SLLM config with gpu_indices."""
        from pylet.config_file import load_and_validate_config

        config_file = tmp_path / "sllm-store.toml"
        config_file.write_text('''
name = "sllm-store"
command = "sllm-store start --port $PORT"

[resources]
target_worker = "gpu-node-0"
gpu_indices = [0, 1, 2, 3]
exclusive = false

[env]
STORAGE_PATH = "/models"

[labels]
type = "sllm-store"
''')
        result = load_and_validate_config(str(config_file))
        assert result.name == "sllm-store"
        assert result.resources.target_worker == "gpu-node-0"
        assert result.resources.gpu_indices == [0, 1, 2, 3]
        assert result.resources.exclusive is False

    def test_minimal_config(self, tmp_path):
        """Test minimal config with just command."""
        from pylet.config_file import load_and_validate_config

        config_file = tmp_path / "simple.toml"
        config_file.write_text('command = "echo hello"')

        result = load_and_validate_config(str(config_file))
        assert result.name == "simple"  # defaults to filename
        assert result.command == "echo hello"


# =============================================================================
# Test: Error Messages
# =============================================================================


class TestErrorMessages:
    """Tests for helpful error messages."""

    def test_unknown_key_suggests_similar(self):
        """Test that unknown key error suggests similar valid key."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {
            "command": "echo hello",
            "resources": {
                "memory_limit": "16Gi",  # should be "memory"
            },
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        error_msg = str(exc_info.value)
        # Should mention the unknown key
        assert "memory_limit" in error_msg
        # Ideally suggests the correct key (nice-to-have)
        # assert "memory" in error_msg  # uncomment when implemented

    def test_type_error_shows_expected_type(self):
        """Test that type error shows expected type."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {
            "command": "echo hello",
            "resources": {
                "gpus": "two",
            },
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        error_msg = str(exc_info.value).lower()
        assert "gpus" in error_msg
        # Should indicate type issue
        assert "int" in error_msg or "type" in error_msg or "integer" in error_msg

    def test_missing_required_field_clear_message(self):
        """Test that missing required field has clear message."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {"name": "no-command"}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        error_msg = str(exc_info.value).lower()
        assert "command" in error_msg
        assert "required" in error_msg or "missing" in error_msg


# =============================================================================
# Test: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_resources_section(self, tmp_path):
        """Test config with empty [resources] section."""
        from pylet.config_file import load_and_validate_config

        config_file = tmp_path / "job.toml"
        config_file.write_text('''
command = "echo hello"

[resources]
# empty
''')
        result = load_and_validate_config(str(config_file))
        assert result.command == "echo hello"

    def test_empty_env_section(self, tmp_path):
        """Test config with empty [env] section."""
        from pylet.config_file import load_and_validate_config

        config_file = tmp_path / "job.toml"
        config_file.write_text('''
command = "echo hello"

[env]
''')
        result = load_and_validate_config(str(config_file))
        assert result.env == {}

    def test_empty_labels_section(self, tmp_path):
        """Test config with empty [labels] section."""
        from pylet.config_file import load_and_validate_config

        config_file = tmp_path / "job.toml"
        config_file.write_text('''
command = "echo hello"

[labels]
''')
        result = load_and_validate_config(str(config_file))
        assert result.labels == {}

    def test_command_array_single_element(self):
        """Test command array with single element."""
        from pylet.config_file import validate_config

        config = {"command": ["python"]}
        result = validate_config(config)
        assert result.command == ["python"]

    def test_command_array_empty_raises(self):
        """Test that empty command array raises error."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {"command": []}
        with pytest.raises(ConfigValidationError):
            validate_config(config)

    def test_gpu_indices_empty_array(self):
        """Test gpu_indices with empty array."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {
            "command": "echo hello",
            "resources": {
                "gpu_indices": [],
            },
        }
        # Empty gpu_indices should probably be an error or treated as "no GPUs"
        # Let's say it's valid but means no GPUs
        result = validate_config(config)
        assert result.resources.gpu_indices == []

    def test_gpus_zero_is_valid(self):
        """Test that gpus=0 is valid (CPU-only job)."""
        from pylet.config_file import validate_config

        config = {
            "command": "echo hello",
            "resources": {"gpus": 0},
        }
        result = validate_config(config)
        assert result.resources.gpus == 0

    def test_gpus_negative_raises(self):
        """Test that negative gpus raises error."""
        from pylet.config_file import validate_config, ConfigValidationError

        config = {
            "command": "echo hello",
            "resources": {"gpus": -1},
        }
        with pytest.raises(ConfigValidationError):
            validate_config(config)

    def test_unicode_in_config(self, tmp_path):
        """Test config with unicode characters."""
        from pylet.config_file import load_and_validate_config

        config_file = tmp_path / "unicode.toml"
        config_file.write_text('''
name = "训练任务"
command = "echo 你好"

[labels]
description = "中文描述"
''')
        result = load_and_validate_config(str(config_file))
        assert result.name == "训练任务"
        assert result.labels["description"] == "中文描述"

    def test_very_long_command(self):
        """Test config with very long command."""
        from pylet.config_file import validate_config

        long_args = " ".join([f"--arg{i} value{i}" for i in range(100)])
        config = {"command": f"python script.py {long_args}"}
        result = validate_config(config)
        assert len(result.command) > 1000
