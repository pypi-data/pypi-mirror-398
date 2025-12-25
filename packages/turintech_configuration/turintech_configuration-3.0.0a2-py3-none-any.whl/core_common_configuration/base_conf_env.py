"""Base configuration module for managing settings overridden by environment variables.

This module defines a base settings class that uses Pydantic's `BaseSettings` to manage
configuration values with a priority system.
"""

# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from pathlib import Path
from typing import Any, Optional, TypeVar, Union

from pydantic import AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import TypeAlias

from core_utils_base.pydantic_utils import new_base_model_class, update_field_default

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#         Defines the public interface of the module that will be imported when using 'from package import *'.         #
#    This helps control what is exposed to the global namespace, limiting imports to only those listed in __all__.     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["PathType", "BaseConfEnv", "BaseConfEnvT", "DefaultsType", "BaseSettingsT"]

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                        Typing                                                        #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

DefaultsType: TypeAlias = Optional[dict]
PathType: TypeAlias = Union[Path, str]

BaseSettingsT = TypeVar("BaseSettingsT", bound=BaseSettings)
BaseConfEnvT = TypeVar("BaseConfEnvT", bound="BaseConfEnv")


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                Module Implementation                                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class BaseConfEnv(BaseSettings):
    """Base class for settings, allowing values to be overridden by environment variables.

    This class establishes a priority order for determining configuration values:
        1. Arguments passed to the class initializer.
        2. Environment variables, e.g., `MY_PREFIX_SPECIAL_FUNCTION`.
        3. Variables loaded from a dotenv (.env) file.
        4. Variables loaded from a secrets directory.
        5. Variables provided in the `defaults` argument.
        6. Default field values specified in the class.
    """

    model_config = SettingsConfigDict(extra="ignore")

    def __init__(
        self,
        _env_file: Optional[PathType] = ".env",
        _env_prefix: Optional[str] = None,
        **values,
    ):
        """Initialize the settings instance.

        Args:
            _env_file (str | Path | None): Path to the dotenv file. Defaults to ".env".
            _env_prefix (str, optional): Prefix for environment variables. Defaults to None.
            **values: Additional values to initialize the instance.
        """
        super().__init__(_env_file=_env_file, _env_prefix=_env_prefix, **values)

    @classmethod
    def with_defaults(
        cls: type[BaseConfEnvT],
        defaults: Optional[dict] = None,
        env_file: Optional[PathType] = ".env",
        env_prefix: Optional[str] = None,
        **initializer_args: Any,
    ) -> BaseConfEnvT:
        """Create a new settings instance with default values applied.

        Args:
            cls (type[BaseConfEnvT]): The class to instantiate.
            defaults (dict | None): A dictionary of default values to apply to fields. Defaults to None.
            env_file (str | Path | None): Path to the dotenv file. Defaults to ".env".
            env_prefix (str | None, optional): Prefix for environment variables. Defaults to None.
            **initializer_args: Additional values to pass to the class initializer.

        Returns:
            BaseConfEnvT: A new instance of the settings class with applied defaults.
        """

        if env_prefix and not env_prefix.endswith("_"):
            env_prefix = f"{env_prefix}_"

        bck = cls.model_config.copy()
        cls.model_config.update({"env_file": env_file})

        new_cls = cls._update_defaults(defaults) if defaults else cls
        new_cls, initializer_args = (
            new_cls._update_alias(env_prefix, **initializer_args) if env_prefix else (new_cls, initializer_args)
        )
        args = {"_env_file": env_file, "_env_prefix": env_prefix, **initializer_args}
        obj = new_cls(**args)

        cls.model_config = bck
        return obj

    @classmethod
    def _update_defaults(cls: type[BaseConfEnvT], defaults: dict) -> type[BaseConfEnvT]:
        """Update the default values of the fields in the class.

        Args:
            cls (type[BaseConfEnvT]): The class to update.
            defaults (dict): A dictionary of default values to apply to fields.

        Returns:
            type[BaseConfEnvT]: A new class with updated field defaults.
        """
        new_annotations = {
            field_name: (
                update_field_default(field=field_info, default=defaults[field_name])
                if field_name in defaults
                else (field_info.annotation, field_info)
            )
            for field_name, field_info in cls.model_fields.items()
        }
        return new_base_model_class(cls=cls, new_annotations=new_annotations)

    @classmethod
    def _update_alias(
        cls: type[BaseConfEnvT], env_prefix: str, **initializer_args: Any
    ) -> tuple[type[BaseConfEnvT], dict]:
        """Update the alias of the fields in the class to include the environment prefix.

        Args:
            cls (type[BaseConfEnvT]): The class to update.
            env_prefix (str): The environment variable prefix to use.

        Returns:
            type[BaseConfEnvT]: A new class with updated field aliases.
        """
        new_cls = new_base_model_class(cls=cls, new_annotations={})
        new_cls.model_config.update({"env_prefix": env_prefix})

        upper_prefix = env_prefix.upper()

        for fname, finfo in new_cls.model_fields.items():
            finfo.validation_alias = AliasChoices(f"{upper_prefix}{fname}".upper())
        new_cls.model_rebuild(force=True)

        initializer_args = {
            f"{upper_prefix}{key}".upper(): value
            for key, value in initializer_args.items()
            if key in new_cls.model_fields.keys()
        }

        return new_cls, initializer_args
