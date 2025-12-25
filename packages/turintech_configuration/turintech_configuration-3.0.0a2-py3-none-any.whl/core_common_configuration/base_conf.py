from typing import Any, Optional, TypeVar

from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["BaseDefaultConfT", "BaseDefaultConf"]


class BaseDefaultConf(BaseSettings):
    """
    Base class for settings, allowing values to be overridden by environment variables.

    Field value priority
        In the case where a value is specified for the same Settings field in multiple ways,
        the selected value is determined as follows (in descending order of priority):
            1. Arguments passed to the Settings class initializer.
            2. Environment variables, e.g. my_prefix_special_function.
            3. Variables loaded from a dotenv (.env) file.
            4. Variables loaded from the secrets directory.
            5. Variables loaded from the 'defaults' argument
            6. The default field values for the Settings model.
    """

    model_config = SettingsConfigDict(extra="ignore")

    def __init__(
        self,
        _env_file: str = ".env",
        defaults: Optional[dict[str, Any]] = None,
        **values: Any,
    ):
        # Arguments passed to the Settings class initializer and Environment variables
        super().__init__(_env_file=_env_file, **values)

        # Initialize None attributes with class defaults
        self._update_empty_values()

    def _update_empty_values(self):
        """
        Updating the attributes for which its value has not been indicated through the environment variables.
        """


BaseDefaultConfT = TypeVar("BaseDefaultConfT", bound=BaseDefaultConf)
