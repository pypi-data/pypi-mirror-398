"""
szproduct.py is the abstract class for all implementations of SzProduct.
"""

from abc import ABC, abstractmethod

from .szhelpers import construct_help

# Metadata

__all__ = ["SzProduct"]
__updated__ = "2025-08-11"

# -----------------------------------------------------------------------------
# SzProduct
# -----------------------------------------------------------------------------


class SzProduct(ABC):
    """
    SzProduct is the definition of the Senzing Python SDK that is
    implemented by packages such as szproduct.py.
    """

    # -------------------------------------------------------------------------
    # Interface definition
    # -------------------------------------------------------------------------

    @abstractmethod
    def get_license(self) -> str:
        """
        The `get_license` method gets the details and entitlements of the applied product license.

        The details do not include the license key.

        Returns:
            str: A JSON document containing Senzing license metadata.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szproduct/get_license.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szproduct/get_license.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def get_version(self) -> str:
        """
        The `get_version` method gets the product version details.

        Returns:
            str: A JSON document containing metadata about the Senzing Engine version being used.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szproduct/get_version.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szproduct/get_version.txt
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
