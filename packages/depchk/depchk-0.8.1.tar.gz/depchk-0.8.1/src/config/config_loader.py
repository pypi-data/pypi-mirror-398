import os
from pathlib import Path
from typing import Any

from chalkbox.components.alert import Alert
from chalkbox.core.console import get_console
from chalkbox.logging.bridge import get_logger
from pydantic import ValidationError
import yaml

from src.config.models import AppConfig

logger = get_logger(__name__)

USER_DIRECTORY_NAME = ".depchk"
BUNDLED_CONFIG_FILENAME = "config.example.yaml"


def get_bundled_config_path() -> Path | None:
    """Find the bundled config.example.yaml file."""
    # When installed, it's at the root of site-packages alongside src/
    src_package_dir = Path(__file__).parent.parent  # src/config -> src
    installed_path = src_package_dir.parent / BUNDLED_CONFIG_FILENAME
    if installed_path.exists():
        return installed_path

    # Development: check project root (3 levels up from src/config/config_loader.py)
    project_root = src_package_dir.parent
    dev_path = project_root / BUNDLED_CONFIG_FILENAME
    if dev_path.exists():
        return dev_path

    return None


def get_bundled_config_content() -> str:
    """Read the bundled config.example.yaml from the package."""
    config_path = get_bundled_config_path()
    if config_path:
        return config_path.read_text()
    raise FileNotFoundError(f"Bundled {BUNDLED_CONFIG_FILENAME} not found")


def is_development_environment() -> bool:
    """
    Detect if running in development mode (poetry run depchk).

    Returns True when both .git directory and pyproject.toml are found in
    ancestor directories, indicating the tool is being run from the project repo.
    """
    try:
        current = Path.cwd()
        while current != current.parent:
            git_dir = current / ".git"
            pyproject = current / "pyproject.toml"

            if git_dir.exists() and pyproject.exists():
                return True

            current = current.parent

        return False
    except Exception:
        return False


def get_user_directory() -> Path:
    """Get user config directory for global installations."""
    return Path.home() / USER_DIRECTORY_NAME


def ensure_user_directory() -> bool:
    """
    Ensure user directory exists for pipx installations.

    Creates:
    - ~/.depchk/
    - ~/.depchk/config.yaml (copied from bundled config.example.yaml)

    Skips creation when running in development mode to avoid polluting user's home directory.
    """
    if is_development_environment():
        return True

    user_dir = get_user_directory()
    config_file = user_dir / "config.yaml"

    try:
        user_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.debug(f"Failed to create user directory: {e}")
        return False

    if not config_file.exists():
        try:
            config_file.write_text(get_bundled_config_content())
        except OSError as e:
            logger.debug(f"Failed to create config file: {e}")
            return False

    return True


def get_default_config_path() -> Path:
    """
    Get default config path based on environment.

    Priority order:
    1. DEVELOPMENT (poetry run depchk): ./config.yaml (project root)
    2. PRODUCTION (pipx install): ~/.depchk/config.yaml

    Auto-creates ~/.depchk/config.yaml only when running via pipx.
    Never creates files in home directory when running in development mode.
    """
    if is_development_environment():
        # Find project root (where pyproject.toml lives)
        current = Path.cwd()
        while current != current.parent:
            pyproject = current / "pyproject.toml"
            if pyproject.exists():
                return current / "config.yaml"
            current = current.parent
        # Fallback to current directory
        return Path.cwd() / "config.yaml"

    ensure_user_directory()
    return get_user_directory() / "config.yaml"


class ConfigLoader:
    def __init__(self, config_path: str | Path | None = None):
        if config_path is None:
            config_path = get_default_config_path()

        self.config_path = Path(config_path)
        self.config: dict[str, Any] = {}
        self._pydantic_config: AppConfig | None = None

    def _create_default_config(self) -> bool:
        """Create default config from bundled config.example.yaml."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(get_bundled_config_content())
            return True
        except OSError as e:
            logger.debug(f"Failed to create default config: {e}")
            return False

    def load(self) -> dict[str, Any]:
        """
        Load configuration from YAML file.

        Auto-creates config from bundled config.example.yaml on first run if not found.
        """
        if not self.config_path.exists() and not self._create_default_config():
            return {}

        try:
            with open(self.config_path, encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}

            return self.config

        except yaml.YAMLError as e:
            console = get_console()
            console.print(Alert.error(f"Failed to parse {self.config_path.name}: {e}"))
            raise

    def load_typed(self) -> AppConfig:
        """Load configuration and return as validated Pydantic model."""
        if not self.config:
            self.load()

        try:
            self._pydantic_config = AppConfig(**self.config)
            return self._pydantic_config

        except ValidationError as e:
            console = get_console()
            console.print(
                Alert.error(
                    f"Configuration validation failed: {e}\n"
                    f"Config file: {self.config_path}\n"
                    "Please check your config.yaml against config.example.yaml"
                )
            )
            raise

    def __repr__(self) -> str:
        return f"ConfigLoader(config_path={self.config_path})"


def load_typed_config(config_path: str | Path | None = None) -> AppConfig:
    """Convenience function to load typed configuration."""
    loader = ConfigLoader(config_path)
    return loader.load_typed()


_config: AppConfig | None = None


def get_config() -> AppConfig:
    """
    Loads from file on first call, then caches the result.
    Supports environment variable overrides.
    """
    global _config
    if _config is None:
        _config = load_typed_config()

        env_overrides = _get_env_overrides()
        if env_overrides:
            _apply_env_overrides(_config, env_overrides)

    return _config


def _get_env_overrides() -> dict[str, Any]:
    overrides: dict[str, Any] = {}

    env_mappings = {
        "DEPCHK_CACHE_TTL": ("analysis", "cache_ttl_hours", int),
        "DEPCHK_ALLOW_PRERELEASE": ("analysis", "allow_prerelease", bool),
    }

    for env_key, (category, key, value_type) in env_mappings.items():
        value_str = os.environ.get(env_key)
        if value_str is not None:
            value: bool | int | str
            if value_type is bool:
                value = value_str.lower() in ("true", "1", "yes")
            elif value_type is int:
                value = int(value_str)
            else:
                value = value_str

            if category not in overrides:
                overrides[category] = {}
            overrides[category][key] = value

    return overrides


def _apply_env_overrides(config: AppConfig, overrides: dict[str, Any]) -> None:
    for category, values in overrides.items():
        section = getattr(config, category, None)
        if section:
            for key, value in values.items():
                setattr(section, key, value)


def set_config(config: AppConfig) -> None:
    global _config
    _config = config


def reset_config() -> None:
    global _config
    _config = None
