"""
This module defines the Application configuration attributes.
"""

# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from typing import Dict, Optional

from pydantic import Field, field_validator

# Internal libraries
from core_common_configuration.base_conf_env import BaseConfEnv, PathType

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["AppConf", "app_conf_factory"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                  APP Configuration                                                   #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class AppConf(BaseConfEnv):
    """Configuration model for application-level settings.

    This class defines the main attributes required to configure an application, such as its name,
    version, deployment environment, group, and identifier.
    All attributes are populated from environment variables, supporting flexible configuration for
    different deployment scenarios.
    """

    name: str = Field(description="The name of the application.")
    version: str = Field(description="The version of the application.")
    env: Optional[str] = Field(default=None, description="Name of the configured deployment environment")
    group: Optional[str] = Field(default=None, description="Name of the group to which the application belongs.")
    id: Optional[str] = Field(default=None, description="Name that identifies the application")

    @field_validator("env")
    def no_hyphen(cls, value: str):
        """We want to remove any hyphen if value is not the empty string."""
        return value[1:] if value and value.startswith("-") else value


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                              APP Configuration Factory                                               #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def app_conf_factory(
    _env_file: Optional[PathType] = None, prefix: Optional[str] = None, defaults: Optional[Dict] = None, **kwargs
) -> AppConf:
    """This is a factory generating a AppConf class specific to a service, loading every value from a generic .env file
    storing variables in uppercase with a service prefix.

        example .env:
           PREFIX_ENV='DEV'
           PREFIX_VERSION='1.0.0'
           ...

    Args:
        _env_file (str): Configuration file of the environment variables from where to load the values.
        prefix (str): Prefix that the class attributes must have in the environment variables.
        defaults (Optional:Dict): New values to override the default field values for the configuration model.
        kwargs (**Dict): Arguments passed to the Settings class initializer.

    Returns:
        conf (AppConf): Object of the required configuration class

    """
    return AppConf.with_defaults(env_file=_env_file, env_prefix=prefix, defaults=defaults, **kwargs)
