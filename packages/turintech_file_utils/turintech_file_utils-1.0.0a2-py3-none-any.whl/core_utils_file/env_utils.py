# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
import os
import re
import subprocess
from collections import ChainMap
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

from dotenv import dotenv_values
from packaging.version import Version
from pydantic.main import BaseModel

from kink import inject


class CondaEnvironmentStorage(BaseModel):
    """
    Model for conda environment storage data.
    """

    name: Optional[str]
    version: Optional[str]
    activated: bool
    path: str


def execute_conda_env_list() -> List[str]:
    """
    Returns the results of running conda env list in a shell environment and splitting lines of result.
    """
    output = subprocess.check_output(["conda", "env", "list"]).decode("utf-8")
    return output.splitlines()


def get_version_from_name(name: str) -> Optional[str]:
    """Extract version from the name of a conda env.

    - Exp: name = example_1.10.1rc4 => output str "1.10.1rc4"
    - The name needs to have all major minor and patch parts to be matched

    """
    version_match = re.search(r"(\d+\.\d+\.\d+(\w+)?(\d+)?)", name)
    return version_match.group(1) if version_match else None


def parse_conda_environment_list(lines: List[str]) -> List[CondaEnvironmentStorage]:
    """Method to parse a list of strings describing outputs of conda listing to
    environments Elements of input list should look like:

    name of env or blank space   |    * (if it is activated) or blank space  |  path to env
    """
    environments: List[CondaEnvironmentStorage] = []

    for line in lines:
        # Ignore lines starting with #
        if line.startswith("#"):
            continue

        # Regular expression for parse the output of one line of `conda env list` command
        # Matches the following:
        #   - name of the environment (optional)
        #   - indicator if the environment is activated (optional)
        #   - path to the environment (required)
        match = re.match(r"\s*(?P<name>\S*)\s+(?P<indicator>\*?)\s*(?P<path>\S+)", line)

        if match:
            name, activated, path = match.groups()

            environments.append(
                CondaEnvironmentStorage(
                    name=name if len(name) else None,
                    activated=bool(activated),
                    path=path,
                    version=get_version_from_name(name),
                )
            )

    return environments


class ICondaEnvFetcher(Protocol):
    def get_latest_conda_env_version(self, conda_env_name: str) -> Optional[str]:
        pass


@inject(alias=ICondaEnvFetcher)
class CondaEnvFetcher(ICondaEnvFetcher):
    def get_latest_conda_env_version(self, conda_env_name: str) -> Optional[str]:
        """
        Returns the latest version of a conda env found.
        """
        # Get conda environment list
        lines = execute_conda_env_list()
        conda_envs_info = parse_conda_environment_list(lines)

        # Extract environment paths and versions
        env_versions = {
            env.path: Version(env.version)
            for env in conda_envs_info
            if Path(env.path).name.startswith(conda_env_name) and env.version is not None
        }

        # If there are no matches return None
        if not env_versions:
            return None

        # Sort by version using the Version class' comparison operators
        latest_env_path = max(env_versions, key=lambda path: env_versions[path])
        latest_env_name = Path(latest_env_path).name
        return latest_env_name


def get_env_variables(prefixes: Tuple[str, ...], env_file: Optional[str] = None) -> ChainMap:
    """Compose a mapping with all environment variables starting with a prefix from `prefixes`, from the system and also
    from an environment variable if provided.

    The environment variables from the system have priority in case of a clash.

    """
    env_file_variables: Dict[str, Any] = {}
    if env_file:
        if not os.path.isfile(env_file):
            raise FileNotFoundError(f"Environment file not found: {env_file}")
        config = dotenv_values(env_file)
        env_file_variables = {k: v for k, v in config.items() if k.startswith(prefixes)}

    os_variables: Dict[str, str] = {key: value for key, value in os.environ.items() if key.startswith(prefixes)}

    # chain all variables
    chain = ChainMap(os_variables, env_file_variables)
    return chain
