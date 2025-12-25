"""
This module implements and instantiates the common configuration class used in the project.
"""

# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Core Source imports
from core_common_configuration.base_conf_env import PathType
from core_common_configuration.base_conf_manager import BaseConfManager

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["ServiceConfManager"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                Configuration Manager                                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class ServiceConfManager(BaseConfManager):
    """
    Configuration Manager class of a service package.
    """

    # APP information
    app_name: str
    app_version: str

    # APP paths
    shared_data_path: Path
    tmp_directory: Path
    root_path: Path
    setup_path: Path
    deploy_path: Path
    data_path: Path

    # The App Configurations object is instantiated once its use is invoked
    defaults_app_conf: Dict[str, Any]

    def __init__(
        self,
        app_name: str,
        root_path: Path,
        app_version: Optional[str] = None,
        setup_path: Optional[Path] = None,
        deploy_path: Optional[Path] = None,
        data_path: Optional[Path] = None,
        shared_data_path: Optional[Path] = None,
        tmp_directory: Optional[Path] = None,
        env_file: Optional[PathType] = None,
        defaults_app_conf: Optional[Dict] = None,
    ):
        self.root_path = root_path.resolve()
        self.setup_path = setup_path or self.root_path / "setup"
        self.deploy_path = deploy_path or self.root_path / "deploy"
        self.data_path = data_path or self.root_path / "data"

        super().__init__(env_file=env_file)

        self.app_name = app_name
        version_file_path: Path = self.setup_path / ".version"
        self.app_version = app_version or version_file_path.read_text().strip() if version_file_path.is_file() else ""
        self.shared_data_path = shared_data_path or Path("/shared-data")
        self.tmp_directory = tmp_directory or self.shared_data_path / "turintech" / app_name.lower()

        self.defaults_app_conf = defaults_app_conf or {"name": self.app_name, "version": self.app_version}

    # --------------------------------------------------------------------------------------------------

    @property
    def env_file(self) -> str:
        """
        Environment configuration file used in the current configuration.
        """
        return self._env_file or ""

    def _retrieve_environment_file(self, env_file: Optional[PathType] = None) -> Tuple[Optional[str], Optional[Path]]:
        return next(
            (
                (str(_env_file), Path(_env_file))
                for _env_file in [env_file, self.root_path / ".env", self.deploy_path / ".env"]
                if _env_file and Path(_env_file).exists()
            ),
            (None, None),
        )
