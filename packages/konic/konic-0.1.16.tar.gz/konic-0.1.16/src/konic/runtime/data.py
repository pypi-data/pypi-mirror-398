"""Data registration for Konic Cloud Platform.

This module provides the data registration mechanism that allows agents
to declare data dependencies. These dependencies are automatically
downloaded and made available as environment variables at training time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from konic.common.errors.cli import KonicValidationError

VersionType = str | Literal["latest"]


@dataclass(frozen=True)
class DataDependency:
    """Represents a registered data dependency.

    Attributes:
        cloud_name: The name of the dataset in Konic Cloud Platform
        env_var: The environment variable name to use for the file path
        version: The version string or "latest" for the current version
    """

    cloud_name: str
    env_var: str
    version: str


_REGISTERED_DATA: list[DataDependency] = []


def register_data(
    cloud_name: str,
    env_var: str,
    version: VersionType = "latest",
) -> DataDependency:
    """
    Register a data dependency for the agent.

    This function declares that the agent requires a specific dataset
    from the Konic Cloud Platform. At training time, the engine will:

    1. Download the dataset (or use cached version if available)
    2. Verify the SHA256 checksum
    3. Set the environment variable to the local file path

    Args:
        cloud_name: The name of the dataset in Konic Cloud Platform.
            Must match an existing dataset uploaded via `konic data push`.
        env_var: The environment variable name that will contain the
            path to the downloaded file. Use this in your environment
            code to access the data.
        version: The version of the dataset to use. Use "latest" to
            always get the most recent version, or specify a specific
            version string (e.g., "1.0.0", "v2", "2024-01-15").

    Returns:
        The created DataDependency object

    Raises:
        KonicValidationError: If cloud_name or env_var is empty

    Example:
        >>> from konic.runtime import register_data
        >>>
        >>> # Register specific version
        >>> register_data("stock-prices", "STOCK_DATA_PATH", "1.0.0")
        >>>
        >>> # Register latest version
        >>> register_data("market-indicators", "INDICATORS_PATH", "latest")
        >>>
        >>> # In your environment code:
        >>> import os
        >>> data_path = os.environ.get("STOCK_DATA_PATH")
        >>> df = pd.read_csv(data_path)
    """
    if not cloud_name:
        raise KonicValidationError(
            "Data cloud_name is required.",
            field="cloud_name",
        )

    if not env_var:
        raise KonicValidationError(
            "Data env_var is required.",
            field="env_var",
        )

    normalized_env_var = env_var.upper().replace("-", "_").replace(" ", "_")

    dependency = DataDependency(
        cloud_name=cloud_name,
        env_var=normalized_env_var,
        version=version,
    )

    _REGISTERED_DATA.append(dependency)
    return dependency


def get_registered_data() -> list[DataDependency]:
    """
    Get all registered data dependencies.

    This function is used internally by the Konic engine to retrieve
    the list of data dependencies that need to be downloaded before
    training starts.

    Returns:
        A list of DataDependency objects. Returns an empty list if
        no data dependencies have been registered.

    Example:
        >>> from konic.runtime import register_data, get_registered_data
        >>>
        >>> register_data("prices", "PRICES_PATH", "1.0.0")
        >>> register_data("indicators", "INDICATORS_PATH", "latest")
        >>>
        >>> deps = get_registered_data()
        >>> for dep in deps:
        ...     print(f"{dep.cloud_name} -> ${dep.env_var} (v{dep.version})")
        prices -> $PRICES_PATH (v1.0.0)
        indicators -> $INDICATORS_PATH (vlatest)
    """
    return _REGISTERED_DATA.copy()


def clear_registered_data() -> None:
    """
    Clear all registered data dependencies.

    This function is primarily used for testing purposes to reset
    the global state between tests.
    """
    global _REGISTERED_DATA
    _REGISTERED_DATA = []
