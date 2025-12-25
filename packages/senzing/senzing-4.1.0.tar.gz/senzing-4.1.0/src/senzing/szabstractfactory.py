"""
szabstractfactory.py is the abstract class for all implementations of SzAbstractFactory.

Implementations:

- `SzAbstractFactoryCore`_
- `SzAbstractFactoryGrpc`_

.. _SzAbstractFactoryCore: https://garage.senzing.com/sz-sdk-python-core/senzing_core.html
.. _SzAbstractFactoryGrpc: https://garage.senzing.com/sz-sdk-python-grpc/senzing_grpc.html
"""

from abc import ABC, abstractmethod

from .szconfigmanager import SzConfigManager
from .szdiagnostic import SzDiagnostic
from .szengine import SzEngine
from .szhelpers import construct_help
from .szproduct import SzProduct

# Metadata

__all__ = ["SzAbstractFactory"]
__updated__ = "2025-08-11"


# -----------------------------------------------------------------------------
# SzAbstractFactory
# -----------------------------------------------------------------------------


class SzAbstractFactory(ABC):
    """
    SzAbstractFactory is the definition of the Senzing Python SDK
    SzAbstractFactory implementations.
    """

    # -------------------------------------------------------------------------
    # Interface definition
    # -------------------------------------------------------------------------

    @abstractmethod
    def create_configmanager(self) -> SzConfigManager:
        """
        The `create_configmanager` method creates a new implementation of an `SzConfigManager` object.

        Args:

        Returns:
            SzConfigManager: A new implementation.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szabstractfactory/create_configmanager.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szabstractfactory/create_configmanager.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def create_diagnostic(self) -> SzDiagnostic:
        """
        The `create_diagnostic` method creates a new implementation of an `SzDiagnostic` object.

        Args:

        Returns:
            SzDiagnostic: A new implementation.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szabstractfactory/create_diagnostic.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szabstractfactory/create_diagnostic.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def create_engine(self) -> SzEngine:
        """
        The `create_engine` method creates a new implementation of an `SzEngine` object.

        Args:

        Returns:
            SzEngine: A new implementation.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szabstractfactory/create_engine.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szabstractfactory/create_engine.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def create_product(self) -> SzProduct:
        """
        The `create_product` method creates a new implementation of an `SzProduct` object.

        Args:

        Returns:
            SzProduct: A new implementation.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szabstractfactory/create_product.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szabstractfactory/create_product.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def destroy(self) -> None:
        """
        The `destroy` method destroys the AbstractFactory and all objects created by the
        AbstractFactory.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szabstractfactory/destroy.py
                :linenos:
                :language: python
        """

    @abstractmethod
    def reinitialize(self, config_id: int) -> None:
        """
        The `reinitialize` method reinitializes the Senzing objects using a specific configuration
        identifier. A list of available configuration identifiers can be retrieved using
        `szconfigmanager.get_config_registry`.

        Args:
            config_id (int): The configuration ID used for the initialization

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szabstractfactory/reinitialize.py
                :linenos:
                :language: python
        """

    # -------------------------------------------------------------------------
    # Convenience methods
    # -------------------------------------------------------------------------

    def help(self, method_name: str = "") -> str:
        """
        Return the help for a particular message.

        Args:
            method_name (str): The name of the method. (e.g. "init"). If empty, a list of methods and descriptions is returned.

        Returns:
            str: The Help information about the requested method
        """
        return construct_help(self, method_name=method_name)
