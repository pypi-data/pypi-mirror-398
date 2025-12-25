"""
szdiagnostic.py is the abstract class for all implementations of SzDiagnostic.
"""

from abc import ABC, abstractmethod

from .szhelpers import construct_help

# Metadata

__all__ = ["SzDiagnostic"]
__updated__ = "2025-08-11"

# -----------------------------------------------------------------------------
# SzDiagnostic
# -----------------------------------------------------------------------------


class SzDiagnostic(ABC):
    """
    Senzing diagnostic module access library
    """

    # -------------------------------------------------------------------------
    # Interface definition
    # -------------------------------------------------------------------------

    @abstractmethod
    def check_repository_performance(self, seconds_to_run: int) -> str:
        """
        The `check_repository_performance` method conducts a rudimentary repository test to gauge I/O
        and network performance.

        Typically, this is only run when troubleshooting performance.

        This is a non-destructive test.

        Args:
            seconds_to_run (int): Duration of the test in seconds.

        Returns:
            str: A string containing a JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szdiagnostic/check_repository_performance.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szdiagnostic/check_repository_performance.txt
                :linenos:
                :language: json
        """

    # NOTE This is experimental and for internal diagnostics, not to be documented
    @abstractmethod
    def get_feature(self, feature_id: int) -> str:  # pylint: disable=empty-docstring
        """Experimental/internal for Senzing support use only."""

    @abstractmethod
    def get_repository_info(self) -> str:
        """
        The `get_repository_info` method returns overview information about the repository.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szdiagnostic/get_repository_info.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szdiagnostic/get_repository_info.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def purge_repository(self) -> None:
        """
        **Warning:**
        The `purge_repository` method purges all data in the repository, except the configuration.

        WARNING: This method is destructive, it will delete all loaded records and entity resolution decisions.

        Senzing does not provide a means to restore the data.

        The only means of recovery would be restoring from a database backup.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szdiagnostic/purge_repository.py
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
