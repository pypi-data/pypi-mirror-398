# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from pathlib import Path
from typing import Any, Optional

from core_common_configuration.base_conf_env import BaseConfEnv, BaseConfEnvT, PathType

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#         Defines the public interface of the module that will be imported when using 'from package import *'.         #
#    This helps control what is exposed to the global namespace, limiting imports to only those listed in __all__.     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["BaseConfManager"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                Module Implementation                                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class BaseConfManager:
    """Manages configuration instances derived from `BaseConfEnv`.

    Enables centralised configuration management, providing methods to load, update,
    and retrieve configurations from environment files and additional parameters.

    Attributes:
        _path_env_file (Path | None): Validated path to the environment file.
        _env_file (str, optional): String representation of the environment file path.
        _config_map (dict[str, BaseConfEnv]): Dictionary of configuration instances.
        _project_map (dict[str, Path]): Dictionary of project paths by name.
    """

    _path_env_file: Optional[Path] = None
    _env_file: Optional[str] = None
    _config_map: dict[str, BaseConfEnv]
    _project_map: dict[str, Path]

    # --------------------------------------------------------------------------------------------------

    def __init__(self, env_file: Optional[PathType] = None):
        """Initialise the configuration manager with optional environment file.

        Args:
            env_file (PathType, optional): Path to the environment file. If None, defaults to no file.
        """
        self._env_file, self._path_env_file = self._retrieve_environment_file(env_file=env_file)
        self._config_map = {}
        self._project_map = {}

    @staticmethod
    def _retrieve_environment_file(env_file: Optional[PathType] = None) -> tuple[Optional[str], Optional[Path]]:
        """Retrieve and validate the provided environment file path.

        Args:
            env_file (PathType, optional): Path to the environment file.

        Returns:
            tuple[str | None, Path | None]: The string and Path object of the environment file.
        """
        _env_file, _path_env_file = (str(env_file), Path(env_file)) if env_file else (None, None)
        return _env_file, _path_env_file

    @property
    def env_file(self) -> Optional[str]:
        """Returns the string representation of the environment file path."""
        return self._env_file

    @property
    def env_file_path(self) -> Optional[Path]:
        """Returns the `Path` object representation of the environment file path."""
        return self._path_env_file

    @property
    def config_map(self) -> dict[str, BaseConfEnv]:
        """Returns the configuration map containing all loaded configuration instances."""
        return self._config_map

    # --------------------------------------------------------------------------------------------------
    # --- Configuration
    # --------------------------------------------------------------------------------------------------

    def get_conf(
        self,
        conf_type: type[BaseConfEnvT],
        conf_name: str,
        env_prefix: Optional[str] = None,
        defaults: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> BaseConfEnvT:
        """Retrieve or create a configuration instance.

        Args:
            conf_type (type[BaseConfEnvT]): Type of configuration to instantiate.
            conf_name (str): Name for the configuration instance.
            env_prefix (str, optional): Optional prefix for environment variables.
            defaults (dict[str, Any] | None): Default values to override in the configuration.
            **kwargs: Additional arguments for the configuration class.

        Returns:
            BaseConfEnvT: The retrieved or newly created configuration instance.

        Raises:
            ValueError: If the configuration type is incompatible with an existing configuration.
        """
        if conf_name not in self._config_map:
            self.update_conf(
                conf_type=conf_type, conf_name=conf_name, env_prefix=env_prefix, defaults=defaults, **kwargs
            )
        elif not isinstance(self._config_map[conf_name], conf_type):
            raise ValueError(
                f"Config error: '{conf_name}' config structure is not compatible with {conf_type.__name__}"
            )
        return self._config_map[conf_name]  # type: ignore

    def update_conf(
        self,
        conf_type: type[BaseConfEnvT],
        conf_name: str,
        env_prefix: Optional[str] = None,
        defaults: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> BaseConfEnvT:
        """Update or create a new configuration instance.

        Args:
            conf_type (type[BaseConfEnvT]): Type of configuration to create or update.
            conf_name (str): Name for the configuration instance.
            env_prefix (str, optional): Optional prefix for environment variables.
            defaults (dict[str, Any] | None): Default values to override in the configuration.
            **kwargs: Additional arguments for the configuration class.

        Returns:
            BaseConfEnvT: The updated or newly created configuration instance.
        """
        conf = conf_type.with_defaults(env_file=self.env_file, env_prefix=env_prefix, defaults=defaults, **kwargs)
        self._config_map[conf_name] = conf
        return conf

    def remove_conf(self, conf_name: str) -> None:
        """Remove a configuration instance from the configuration map.

        Args:
            conf_name (str): The name of the configuration instance to remove.
        """
        self._config_map.pop(conf_name, None)

    # --------------------------------------------------------------------------------------------------
    # --- Project Paths
    # --------------------------------------------------------------------------------------------------

    def get_project_path(self, key: str) -> Optional[Path]:
        """Retrieve a project path from the project map.

        Args:
            key (str): Key identifying the project path.

        Returns:
            Path | None: The project path associated with the key, or None if not found.
        """
        return self._project_map.get(key)

    def set_project_path(self, key: str, path: PathType) -> None:
        """Add or update a project path in the project map.

        Args:
            key (str): Key identifying the project path.
            path (PathType): Path to associate with the key.
        """
        resolved_path = Path(path).resolve()
        self._project_map[key] = resolved_path

    def remove_project_path(self, key: str) -> None:
        """Remove a project path from the project map.

        Args:
            key (str): Key identifying the project path to remove.
        """
        self._project_map.pop(key, None)
