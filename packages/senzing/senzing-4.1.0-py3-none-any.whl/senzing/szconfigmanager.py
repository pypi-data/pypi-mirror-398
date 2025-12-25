"""
szconfigmanager.py is the abstract class for all implementations of SzConfigManager.
"""

from abc import ABC, abstractmethod

from .szconfig import SzConfig
from .szhelpers import construct_help

# Metadata

__all__ = ["SzConfigManager"]
__updated__ = "2025-08-11"

# -----------------------------------------------------------------------------
# SzConfigManager
# -----------------------------------------------------------------------------


class SzConfigManager(ABC):
    """
    SzConfigManager is the definition of the Senzing Python SDK that is
    implemented by packages such as szconfigmanager.py.
    """

    # -------------------------------------------------------------------------
    # Interface definition
    # -------------------------------------------------------------------------

    @abstractmethod
    def create_config_from_config_id(self, config_id: int) -> SzConfig:
        """
        The `create_config_from_config_id` method creates a new SzConfig instance for a configuration ID.

        Args:
            config_id (int): The configuration identifier of the desired Senzing configuration to retrieve.

        Returns:
            SzConfig: Represents an in-memory Senzing configuration that can be modified.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szconfigmanager/create_config_from_config_id.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szconfigmanager/create_config_from_config_id.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def create_config_from_string(self, config_definition: str) -> SzConfig:
        """
        The `create_config_from_string` method creates a new SzConfig instance from a configuration definition.

        Args:
            config_definition (str): The Senzing configuration JSON document.

        Returns:
            SzConfig: Represents an in-memory Senzing configuration that can be modified.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szconfigmanager/create_config_from_string.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szconfigmanager/create_config_from_string.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def create_config_from_template(self) -> SzConfig:
        """
        The `create_config_from_template` method creates a new SzConfig instance from the template
        configuration definition.

        Args:
            config_definition (str): The Senzing configuration JSON document.

        Returns:
            SzConfig: Represents an in-memory Senzing configuration that can be modified.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szconfigmanager/create_config_from_template.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szconfigmanager/create_config_from_template.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def get_config_registry(self) -> str:
        """
        The `get_config_registry` method gets the configuration registry.

        The registry contains the original timestamp, original comment, and configuration ID
        of all configurations ever registered with the repository.

        Registered configurations cannot be unregistered.

        Returns:
            str: A JSON document containing Senzing configurations.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szconfigmanager/get_config_registry.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szconfigmanager/get_config_registry.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def get_default_config_id(self) -> int:
        """
        The `get_default_config_id` method gets the default configuration ID for the repository.

        Unless an explicit configuration ID is specified at initialization, the default configuration ID is used.

        This may not be the same as the active configuration ID.

        Returns:
            int:  The current default configuration ID or zero if the default configuration has not been set.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szconfigmanager/get_default_config_id.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szconfigmanager/get_default_config_id.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def register_config(self, config_definition: str, config_comment: str) -> int:
        """
        The `register_config` method registers a configuration definition in the repository.

        Registered configurations do not become immediately active nor do they become the default.

        Registered configurations cannot be unregistered.

        Args:
            config_definition (str): The Senzing configuration JSON document.
            config_comment (str):  free-form string of comments describing the configuration document.

        Returns:
            int: A configuration identifier.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szconfigmanager/register_config.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szconfigmanager/register_config.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def replace_default_config_id(self, current_default_config_id: int, new_default_config_id: int) -> None:
        """
        The `replace_default_config_id` method replaces the existing default configuration ID with
        a new configuration ID.

        The change is prevented if the current default configuration ID value is not as expected.

        Use this in place of set_default_config_id() to handle race conditions.

        Args:
            current_default_config_id (int): The configuration identifier to replace.
            new_default_config_id (int): The configuration identifier to use as the default.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szconfigmanager/replace_default_config_id.py
                :linenos:
                :language: python
        """

    @abstractmethod
    def set_default_config(self, config_definition: str, config_comment: str) -> int:
        """
        The `set_default_config` method registers a configuration in the repository and sets its ID as the default
        for the repository.

        Convenience method for register_config() followed by set_default_config_id().

        Args:
            config_definition (str): The Senzing configuration JSON document.
            config_comment (str):  free-form string of comments describing the configuration document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szconfigmanager/set_default_config.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szconfigmanager/set_default_config.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def set_default_config_id(self, config_id: int) -> None:
        """
        The `set_default_config_id` method sets the default configuration ID.

        Usually this method is sufficient for setting the default configuration ID.
        However in concurrent environments that could encounter race conditions,
        consider using replace_default_config_id() instead.

        Args:
            config_id (int): The configuration identifier of the Senzing Engine configuration to use as the default.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szconfigmanager/set_default_config_id.py
                :linenos:
                :language: python
        """

    # -------------------------------------------------------------------------
    # Convenience methods
    # -------------------------------------------------------------------------

    def help(self, method_name: str = "") -> str:
        """
        The `help` method returns help for a particular message.

        Args:
            method_name (str): The name of the method. (e.g. "init"). If empty, a list of methods and descriptions is returned.

        Returns:
            str: The Help information about the requested method
        """
        return construct_help(self, method_name=method_name)
