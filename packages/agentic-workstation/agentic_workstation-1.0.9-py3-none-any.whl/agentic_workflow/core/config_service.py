"""Assemble the five-layer configuration cascade into a merged RuntimeConfig.

Layers: defaults, user-global, project-local, workflow definition, runtime flags.

1. Defaults (hardcoded)
2. User Global (~/.config/agentic/config.yaml)
3. Project Local (<project>/.agentic/config.yaml)
4. Workflow Definition (workflow.json)
5. Runtime Flags (CLI args)
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional, TypedDict, Any
import yaml
import platformdirs
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from .schema import SystemConfig, ProjectConfig, WorkflowRules, RuntimeConfig
from .exceptions import ConfigError
from .paths import find_project_root
import logging

logger = logging.getLogger(__name__)

__all__ = ["ConfigurationService"]


class RawConfig(TypedDict, total=False):
    """Typed mapping representing raw configuration data loaded from files.

    This TypedDict is permissive (total=False) and used to avoid untyped
    `dict`/`Any` annotations in public APIs while retaining flexible keys.
    """


class ConfigurationService:
    """Load and merge the five-layer configuration cascade into RuntimeConfig.

    Responsible for loading defaults, user global, project-level, workflow
    definitions, and runtime flags into a single `RuntimeConfig` instance.
    """

    def __init__(self, console: Any = None, input_handler: Any = None, feedback: Any = None, layout: Any = None) -> None:
        """Initialize the ConfigurationService with optional TUI dependencies."""
        self.console = console
        self.input_handler = input_handler
        self.feedback = feedback
        self.layout = layout
        self.global_config_path = self._get_global_config_path()

    def _get_user_config_dir(self) -> Path:
        """Return the user config directory path."""
        return Path(platformdirs.user_config_dir("agentic", "agentic"))

    def _get_global_config_path(self) -> Path:
        """Return the global config file path under the user's config directory."""
        config_dir = self._get_user_config_dir()
        return config_dir / "config.yaml"

    def ensure_system_configured(self, console: Any = None, input_handler: Any = None, feedback: Any = None, layout: Any = None) -> None:
        """Ensure Layer 2 (global) config exists, running setup if interactive."""
        if not self.global_config_path.exists():
            if sys.stdin.isatty() and sys.stdout.isatty():
                from ..cli.tui.setup import run_setup_wizard
                run_setup_wizard(
                    console_override=console or self.console,
                    input_handler=input_handler or self.input_handler,
                    feedback=feedback or self.feedback,
                )
            else:
                # Headless fallback: create default config
                self._create_default_config()

    def _create_default_config(self) -> None:
        """Write a default global `SystemConfig` to disk for headless setups."""
        try:
            config = SystemConfig()
            self.global_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.global_config_path, "w") as f:
                yaml.dump(config.model_dump(), f, default_flow_style=False)
        except Exception as e:
            raise ConfigError(f"Failed to create default config: {e}")

    def load_config(
        self,
        context_path: Optional[Path] = None,
        verbose: bool = False,
        force: bool = False,
        console: Any = None,
        input_handler: Any = None,
        feedback: Any = None,
        layout: Any = None,
    ) -> RuntimeConfig:
        """Load and return the merged `RuntimeConfig` assembled from all layers."""
        self.ensure_system_configured(console=console, input_handler=input_handler, feedback=feedback, layout=layout)

        config = RuntimeConfig(verbose=verbose, force=force)

        # Layer 1: Defaults already provided by RuntimeConfig

        # Layer 2: User Global
        if self.global_config_path.exists():
            global_data = self._load_yaml(self.global_config_path)
            config.system = SystemConfig(**global_data)

        # Layer 3 & 4: Project and Workflow
        project_root = find_project_root(context_path)
        if project_root:
            # Project config from <project>/.agentic/config.yaml
            project_config_path = project_root / ".agentic" / "config.yaml"
            if project_config_path.exists():
                project_data = self._load_yaml(project_config_path)
                project_data['root_path'] = str(project_root)  # Add root_path
                config.project = ProjectConfig(**project_data)

                # Workflow rules (Layer 4)
                workflow_name = config.project.workflow
                from ..generation.canonical_loader import load_canonical_workflow
                workflow_data = load_canonical_workflow(workflow_name)
                config.workflow_rules = WorkflowRules(**workflow_data.get("workflow", {}))

        return config

    def _load_yaml(self, path: Path) -> RawConfig:
        """Read a YAML file and return a typed `RawConfig` mapping.

        Uses `yaml.safe_load` and normalizes the result to an empty mapping
        when the file contains no data. Raises `ConfigError` on failure.
        """
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigError(f"Failed to load config from {path}: {e}")

    def _load_toml(self, path: Path) -> RawConfig:
        """Read a TOML file and return a typed `RawConfig` mapping.

        Uses `tomllib` (or `tomli` fallback) to parse TOML data and returns
        an empty mapping when no data is present. Raises `ConfigError` on failure.
        """
        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except Exception as e:
            raise ConfigError(f"Failed to load config from {path}: {e}")

    def deep_merge(self, base: RawConfig, overlay: RawConfig) -> RawConfig:
        """Deep-merge two raw configuration mappings and return the merged mapping.

        This performs a recursive merge where nested mappings are merged
        rather than overwritten. Overlay values that are `None` or empty
        strings are ignored so they do not clobber existing settings.
        """
        def is_empty(val: Any) -> bool:
            return val is None or (isinstance(val, str) and val == "")

        # Start with base, dropping empty values so they don't linger.
        result: RawConfig = {
            key: value
            for key, value in base.items()
            if not is_empty(value)
        }

        for key, value in overlay.items():
            if is_empty(value):
                # Skip empty overlay values; they should not override prior settings.
                continue
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Type ignore: recursive TypedDict mapping merging at runtime
                result[key] = self.deep_merge(result[key], value)  # type: ignore[arg-type]
            else:
                result[key] = value  # type: ignore[assignment]
        return result


# Standalone utility functions for backward compatibility
# Note: These have been moved to core/paths.py for consolidation
