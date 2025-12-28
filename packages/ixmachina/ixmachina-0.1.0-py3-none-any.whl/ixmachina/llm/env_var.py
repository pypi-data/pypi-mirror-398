"""
Environment variable handling for credentials.
"""

import os
from typing import Optional


class EnvVar:
    """
    Represents an environment variable name.

    When used with LLM class, the actual value will be read from
    the environment variables.
    """

    def __init__(self, name: str, default: Optional[str] = None) -> None:
        """
        Initialize an environment variable reference.

        Args:
            name: The name of the environment variable.
            default: Optional default value if the environment variable is not set.
        """
        self.name = name
        self.default = default

    def get_value(self) -> str:
        """
        Get the value from the environment variable.

        Returns:
            The environment variable value.

        Raises:
            ValueError: If the environment variable is not set and no default is provided.
        """
        value = os.getenv(self.name, self.default)
        if value is None:
            raise ValueError(
                f"Environment variable '{self.name}' is not set and no default value provided"
            )
        return value

    def __str__(self) -> str:
        """Return string representation."""
        return f"EnvVar(name='{self.name}')"

    def __repr__(self) -> str:
        """Return representation."""
        return self.__str__()

