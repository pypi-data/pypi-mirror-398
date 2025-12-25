"""
szconfig.py is the abstract class for all implementations of SzConfig.
"""

from abc import ABC, abstractmethod

from .szhelpers import construct_help

# Metadata

__all__ = ["SzConfig"]
__updated__ = "2025-08-11"

# -----------------------------------------------------------------------------
# SzConfig
# -----------------------------------------------------------------------------


class SzConfig(ABC):
    """
    SzConfig is the definition of the Senzing Python SDK that is
    implemented by packages such as szconfig.py.
    """

    # -------------------------------------------------------------------------
    # Interface definition
    # -------------------------------------------------------------------------

    @abstractmethod
    def export(self) -> str:
        """
        The `export` method retrieves the definition for this configuration.

        Args:

        Returns:
            str: A string containing a JSON Document representation of the Senzing SzConfig object.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szconfig/export.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szconfig/export.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def get_data_source_registry(self) -> str:
        """
        The `get_data_source_registry` method gets the data source registry for this configuration.

        Args:

        Returns:
            str: A string containing a JSON document listing all of the data sources.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szconfig/get_data_source_registry.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szconfig/get_data_source_registry.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def register_data_source(self, data_source_code: str) -> str:
        """
        The `register_data_source` method adds a data source to this configuration.

        Because SzConfig is an in-memory representation, the repository is not changed
        unless the configuration is exported and then registered via ConfigManager.

        Args:
            data_source_code (str): Name of data source code to add.

        Returns:
            str: A string containing a JSON document listing the newly created data source.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szconfig/register_data_source.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szconfig/register_data_source.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def unregister_data_source(self, data_source_code: str) -> str:
        """
        The `unregister_data_source` method removes a data source from this configuration.

        Because SzConfig is an in-memory representation, the repository is not changed unless
        the configuration is exported and then registered via ConfigManager.

        Is idempotent.

        Warning: If records in the repository refer to the unregistered datasource,
        the configuration cannot be used as the active configuration.

        Args:
            data_source_code (str): Name of data source code to delete.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szconfig/unregister_data_source.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szconfig/unregister_data_source.txt
                :linenos:
                :language: json
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
