"""Configuration management for Todo CLI."""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import yaml


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "todo-cli" / "config.yaml"

# Valid values for config options
VALID_PRIORITIES = {"p0", "p1", "p2", "p3", "0", "1", "2", "3"}
VALID_DATE_FORMATS = {"YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "DD-MM-YYYY"}
VALID_TIME_FORMATS = {"12h", "24h"}
VALID_COLOR_SCHEMES = {"auto", "dark", "light", "none"}


@dataclass
class Config:
    """Todo CLI configuration."""

    # Display settings
    default_priority: str = "p2"
    date_format: str = "YYYY-MM-DD"
    time_format: str = "24h"
    color_scheme: str = "auto"  # auto, dark, light, none

    # Behavior settings
    confirm_delete: bool = True
    auto_start_on_add: bool = False
    show_completed_in_list: bool = False

    # Database location (can be customized)
    db_path: Optional[str] = None

    def validate(self) -> list[str]:
        """Validate config values and return list of warnings."""
        warnings = []

        if self.default_priority.lower() not in VALID_PRIORITIES:
            warnings.append(
                f"Invalid default_priority '{self.default_priority}'. "
                f"Valid: {', '.join(sorted(VALID_PRIORITIES))}. Using 'p2'."
            )

        if self.date_format not in VALID_DATE_FORMATS:
            warnings.append(
                f"Invalid date_format '{self.date_format}'. "
                f"Valid: {', '.join(sorted(VALID_DATE_FORMATS))}. Using 'YYYY-MM-DD'."
            )

        if self.time_format not in VALID_TIME_FORMATS:
            warnings.append(
                f"Invalid time_format '{self.time_format}'. "
                f"Valid: {', '.join(sorted(VALID_TIME_FORMATS))}. Using '24h'."
            )

        if self.color_scheme.lower() not in VALID_COLOR_SCHEMES:
            warnings.append(
                f"Invalid color_scheme '{self.color_scheme}'. "
                f"Valid: {', '.join(sorted(VALID_COLOR_SCHEMES))}. Using 'auto'."
            )

        if not isinstance(self.confirm_delete, bool):
            warnings.append(
                f"Invalid confirm_delete '{self.confirm_delete}'. Must be true/false. Using true."
            )

        if not isinstance(self.auto_start_on_add, bool):
            warnings.append(
                f"Invalid auto_start_on_add '{self.auto_start_on_add}'. Must be true/false. Using false."
            )

        if not isinstance(self.show_completed_in_list, bool):
            warnings.append(
                f"Invalid show_completed_in_list '{self.show_completed_in_list}'. Must be true/false. Using false."
            )

        return warnings

    @classmethod
    def load(cls, config_path: Optional[Path] = None, validate: bool = True) -> tuple["Config", list[str]]:
        """Load configuration from YAML file.

        Returns tuple of (config, warnings).
        """
        path = config_path or DEFAULT_CONFIG_PATH
        warnings = []

        if not path.exists():
            return cls(), []

        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            config = cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
            if validate:
                warnings = config.validate()
            return config, warnings
        except Exception as e:
            warnings.append(f"Error loading config: {e}. Using defaults.")
            return cls(), warnings

    def save(self, config_path: Optional[Path] = None) -> Path:
        """Save configuration to YAML file."""
        path = config_path or DEFAULT_CONFIG_PATH
        path.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(self)
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return path

    def get_db_path(self) -> Path:
        """Get database path from config or default."""
        if self.db_path:
            return Path(self.db_path).expanduser()
        return Path.home() / ".local" / "share" / "todo-cli" / "todos.db"

    def get_date_format_str(self) -> str:
        """Convert config date format to strftime format."""
        formats = {
            "YYYY-MM-DD": "%Y-%m-%d",
            "MM/DD/YYYY": "%m/%d/%Y",
            "DD/MM/YYYY": "%d/%m/%Y",
            "DD-MM-YYYY": "%d-%m-%Y",
        }
        return formats.get(self.date_format, "%Y-%m-%d")

    def get_time_format_str(self) -> str:
        """Convert config time format to strftime format."""
        if self.time_format == "12h":
            return "%I:%M %p"
        return "%H:%M"


# Global config instance and warnings
_config: Optional[Config] = None
_config_warnings: list[str] = []


def get_config() -> Config:
    """Get the global config instance."""
    global _config, _config_warnings
    if _config is None:
        _config, _config_warnings = Config.load()
    return _config


def get_config_warnings() -> list[str]:
    """Get any warnings from loading config."""
    return _config_warnings


def reload_config() -> Config:
    """Reload config from file."""
    global _config, _config_warnings
    _config, _config_warnings = Config.load()
    return _config


def save_config(config: Config) -> Path:
    """Save config and update global instance."""
    global _config, _config_warnings
    path = config.save()
    _config = config
    _config_warnings = []  # Clear warnings after saving valid config
    return path
