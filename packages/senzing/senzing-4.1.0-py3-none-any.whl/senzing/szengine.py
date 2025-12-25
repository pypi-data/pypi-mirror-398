"""
szengine.py is the abstract class for all implementations of SzEngine.
"""

# pylint: disable=C0302

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from .szengineflags import SzEngineFlags
from .szhelpers import construct_help

# Metadata

__all__ = ["SzEngine"]
__updated__ = "2025-08-11"


# -------------------------------------------------------------------------
# Classes
# -------------------------------------------------------------------------


class SzEngine(ABC):
    """
    Senzing engine module access library
    """

    # -------------------------------------------------------------------------
    # Interface definition
    # -------------------------------------------------------------------------

    @abstractmethod
    def add_record(
        self,
        data_source_code: str,
        record_id: str,
        record_definition: str,
        flags: int = SzEngineFlags.SZ_ADD_RECORD_DEFAULT_FLAGS,
    ) -> str:
        """
        The `add_record` method loads a record into the repository and performs entity resolution.

        If a record already exists with the same data source code and record ID, it will be replaced.

        If the record definition contains DATA_SOURCE and RECORD_ID JSON keys,
        the values must match the dataSourceCode and recordID parameters.

        The data source code must be registered in the active configuration.

        Args:
            data_source_code (str): Identifies the provenance of the data.
            record_id (str): The unique identifier within the records of the same data source.
            record_definition (str): A JSON document containing the record to be added to the Senzing repository.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_ADD_RECORD_DEFAULT_FLAGS.

        Returns:
            str: If flags are set to return the WITH_INFO response a JSON document containing the details, otherwise an empty string.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/add_record.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/add_record.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def close_export_report(self, export_handle: int) -> None:
        """
        The `close_export_report` method closes an export report.

        Used in conjunction with export_json_entity_report(), export_csv_entity_report(), and fetch_next().

        Args:
            export_handle (int): A handle created by `export_json_entity_report` or `export_csv_entity_report`.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/export_json_fetch_close.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/export_json_fetch_close.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def count_redo_records(self) -> int:
        """
        The `count_redo_records` method gets the number of redo records pending processing.

        WARNING: When there is a large number of redo records, this is an expensive call.
        Hint: If processing redo records, use result of `get_redo_record` to manage looping.

        Returns:
            int: The number of redo records in Senzing's redo queue.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/count_redo_records.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/count_redo_records.txt
                :linenos:
                :language: guess
        """

    @abstractmethod
    def delete_record(
        self,
        data_source_code: str,
        record_id: str,
        flags: int = SzEngineFlags.SZ_DELETE_RECORD_DEFAULT_FLAGS,
    ) -> str:
        """
        The `delete_record` method deletes a record from the repository and performs entity resolution.

        The data source code must be registered in the active configuration.

        Is idempotent.

        Args:
            data_source_code (str): Identifies the provenance of the data.
            record_id (str): The unique identifier within the records of the same data source.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_DELETE_RECORD_DEFAULT_FLAGS.

        Returns:
            str: If flags are set to return the WITH_INFO response a JSON document containing the details, otherwise an empty string.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/delete_record.py
                :linenos:

            **Output:**

            .. literalinclude:: ../../examples/szengine/delete_record.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def export_csv_entity_report(
        self,
        csv_column_list: str,
        flags: int = SzEngineFlags.SZ_EXPORT_DEFAULT_FLAGS,
    ) -> int:
        """
        The `export_csv_entity_report` method initiates an export report of entity data in CSV format.

        Used in conjunction with fetch_next() and close_entity_report().

        The first fetch_next() call, after calling this method, returns the CSV header.

        Subsequent fetch_next() calls return exported entity data in CSV format.

        WARNING: This method should only be used on systems containing less than a few million records. For larger systems, see https://www.senzing.com/docs/tutorials/advanced_replication/

        Args:
            csv_column_list (str): A comma-separated list of column names for the CSV export.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_EXPORT_DEFAULT_FLAGS.

        Returns:
            int: A handle that identifies the document to be scrolled through using `fetch_next`.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/export_csv_fetch_close.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/export_csv_fetch_close.txt
                :linenos:
                :language: guess
        """

    @abstractmethod
    def export_json_entity_report(self, flags: int = SzEngineFlags.SZ_EXPORT_DEFAULT_FLAGS) -> int:
        """
        The `export_json_entity_report` method initiates an export report of entity data in JSON Lines format.

        Used in conjunction with fetch_next() and close_entity_report().

        Each fetch_next() call returns exported entity data as a JSON object.

        WARNING: This method should only be used on systems containing less than a few million records. For larger systems, see https://www.senzing.com/docs/tutorials/advanced_replication/

        Args:
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_EXPORT_DEFAULT_FLAGS.

        Returns:
            int: A handle that identifies the document to be scrolled through using `fetch_next`.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/export_json_fetch_close.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/export_json_fetch_close.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def fetch_next(self, export_handle: int) -> str:
        """
        The `fetch_next` method fetches the next line of entity data from an open export report.

        Used in conjunction with export_json_entity_report(), export_csv_entity_report(), and close_entity_report().

        If the export handle was obtained from export_csv_entity_report(),
        this returns the CSV header on the first call and exported entity data in CSV format on subsequent calls.

        If the export handle was obtained from export_json_entity_report(),
        this returns exported entity data as a JSON object.

        When None is returned, the export report is complete
        and the caller should invoke close_entity_report() to free resources.

        Args:
            export_handle (int): A handle created by `export_json_entity_report` or `export_json_entity_report`.

        Returns:
            str: Entity data for an export report.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/export_json_fetch_close.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/export_json_fetch_close.txt
                :linenos:
                :language: json
        """

    # pylint: disable=empty-docstring
    # NOTE - Not to be documented or examples, early adaptor feature, needs manual additions to config
    @abstractmethod
    def find_interesting_entities_by_entity_id(
        self, entity_id: int, flags: int = SzEngineFlags.SZ_FIND_INTERESTING_ENTITIES_DEFAULT_FLAGS
    ) -> str:
        """
        Experimental method.

        Contact Senzing support.
        """

    # NOTE - Not to be documented or examples, early adaptor feature, needs manual additions to config
    @abstractmethod
    def find_interesting_entities_by_record_id(
        self,
        data_source_code: str,
        record_id: str,
        flags: int = SzEngineFlags.SZ_FIND_INTERESTING_ENTITIES_DEFAULT_FLAGS,
    ) -> str:
        """
        Experimental method.

        Contact Senzing support.
        """

    # pylint: enable=empty-docstring

    @abstractmethod
    def find_network_by_entity_id(
        self,
        entity_ids: List[int],
        max_degrees: int,
        build_out_degrees: int,
        build_out_max_entities: int,
        flags: int = SzEngineFlags.SZ_FIND_NETWORK_DEFAULT_FLAGS,
    ) -> str:
        """
        The `find_network_by_entity_id` method retrieves a network of relationships among entities,
        specified by entity IDs.

        Warning: Entity networks may be very large due to the volume of inter-related data in the repository.
        The parameters of this method can be used to limit the information returned.

        Args:
            entity_ids (list(int)): The entity IDs to find the network between.
            max_degrees (int): The maximum number of degrees in paths between search entities.
            build_out_degrees (int): The number of degrees of relationships to show around each search entity.
            build_out_max_entities (int): The maximum number of entities to return in the discovered network.
            flags (int, optional): The maximum number of entities to return in the discovered network. Defaults to SzEngineFlags.SZ_FIND_NETWORK_DEFAULT_FLAGS.

        Returns:
            str: A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/find_network_by_entity_id.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/find_network_by_entity_id.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def find_network_by_record_id(
        self,
        record_keys: List[Tuple[str, str]],
        max_degrees: int,
        build_out_degrees: int,
        build_out_max_entities: int,
        flags: int = SzEngineFlags.SZ_FIND_NETWORK_DEFAULT_FLAGS,
    ) -> str:
        """
        The `find_network_by_record_id` method retrieves a network of relationships among entities,
        specified by record IDs.

        Warning: Entity networks may be very large due to the volume of inter-related data in the repository.
        The parameters of this method can be used to limit the information returned.

        Args:
            record_keys (list(tuple(str, str))): The data source codes and record IDs to find the network between.
            max_degrees (int): The maximum number of degrees in paths between search entities.
            build_out_degrees (int): The number of degrees of relationships to show around each search entity.
            build_out_max_entities (int): The maximum number of entities to return in the discovered network.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_FIND_NETWORK_DEFAULT_FLAGS.

        Returns:
            str: A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/find_network_by_record_id.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/find_network_by_record_id.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def find_path_by_entity_id(
        self,
        start_entity_id: int,
        end_entity_id: int,
        max_degrees: int,
        avoid_entity_ids: Optional[List[int]] = None,
        required_data_sources: Optional[List[str]] = None,
        flags: int = SzEngineFlags.SZ_FIND_PATH_DEFAULT_FLAGS,
    ) -> str:
        """
        The `find_path_by_entity_id` method searches for the shortest relationship path between two entities,
        specified by entity IDs.

        The returned path is the shortest path among the paths that satisfy the parameters.

        Args:
            start_entity_id (int): The entity ID for the starting entity of the search path.
            end_entity_id (int): The entity ID for the ending entity of the search path.
            max_degrees (int): The maximum number of degrees in paths between search entities.
            avoid_entity_ids (list(int), optional): The entity IDs to avoid when finding a path.
            required_data_sources (list(str), optional): The data source code(s) that must be in a path.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_FIND_PATH_DEFAULT_FLAGS.

        Returns:
            str: A JSON document with an ENTITY_PATHS section that details the path between the entities.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/find_path_by_entity_id.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/find_path_by_entity_id.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def find_path_by_record_id(
        self,
        start_data_source_code: str,
        start_record_id: str,
        end_data_source_code: str,
        end_record_id: str,
        max_degrees: int,
        avoid_record_keys: Optional[List[Tuple[str, str]]] = None,
        required_data_sources: Optional[List[str]] = None,
        flags: int = SzEngineFlags.SZ_FIND_PATH_DEFAULT_FLAGS,
    ) -> str:
        """
        The `find_path_by_record_id` method searches for the shortest relationship path between two entities,
        specified by record IDs.

        The returned path is the shortest path among the paths that satisfy the parameters.

        Args:
            start_data_source_code (str): Identifies the provenance of the record for the starting entity of the search path.
            start_record_id (str): The unique identifier within the records of the same data source for the starting entity of the search path.
            end_data_source_code (str): Identifies the provenance of the record for the ending entity of the search path.
            end_record_id (str): The unique identifier within the records of the same data source for the ending entity of the search path.
            max_degrees (int): The maximum number of degrees in paths between search entities.
            avoid_record_keys (list(tuple(str, str)), optional): The data source codes and record IDs to avoid when finding a path.
            required_data_sources (list(str), optional): The data source code(s) that must be in a path.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_FIND_PATH_DEFAULT_FLAGS.

        Returns:
            str: A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/find_path_by_record_id.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/find_path_by_record_id.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def get_active_config_id(self) -> int:
        """
        The `get_active_config_id` method gets the currently active configuration ID.

        May not be the default configuration ID.

        Returns:
            int: The identifier of the active Senzing Engine configuration.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/get_active_config_id.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/get_active_config_id.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def get_entity_by_entity_id(
        self,
        entity_id: int,
        flags: int = SzEngineFlags.SZ_ENTITY_DEFAULT_FLAGS,
    ) -> str:
        """
        The `get_entity_by_entity_id` method retrieves information about an entity, specified by entity ID.

        Args:
            entity_id (int): The unique identifier of an entity.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_ENTITY_DEFAULT_FLAGS.

        Returns:
            str: A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/get_entity_by_entity_id.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/get_entity_by_entity_id.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def get_entity_by_record_id(
        self,
        data_source_code: str,
        record_id: str,
        flags: int = SzEngineFlags.SZ_ENTITY_DEFAULT_FLAGS,
    ) -> str:
        """
        The `get_entity_by_record_id` method retrieves information about an entity, specified by record ID.

        Args:
            data_source_code (str): Identifies the provenance of the data.
            record_id (str): The unique identifier within the records of the same data source.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_ENTITY_DEFAULT_FLAGS.

        Returns:
            str: A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/get_entity_by_record_id.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/get_entity_by_record_id.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def get_record(
        self,
        data_source_code: str,
        record_id: str,
        flags: int = SzEngineFlags.SZ_RECORD_DEFAULT_FLAGS,
    ) -> str:
        """
        The `get_record` method retrieves information about a record.

        The information contains the original record data that was loaded and may contain other information depending
        on the flags parameter.

        Args:
            data_source_code (str): Identifies the provenance of the data.
            record_id (str): The unique identifier within the records of the same data source.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_RECORD_DEFAULT_FLAGS.

        Returns:
            str: A JSON document of a single record.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/get_record.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/get_record.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def get_record_preview(
        self,
        record_definition: str,
        flags: int = SzEngineFlags.SZ_RECORD_PREVIEW_DEFAULT_FLAGS,
    ) -> str:
        """
        The `get_record_preview` method describes the features resulting from the hypothetical load of a record.

        Used to preview the features for a record that has not been loaded.

        Args:
            record_definition (str): A JSON document containing the record to be tested.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_RECORD_PREVIEW_DEFAULT_FLAGS.

        Returns:
            str: A JSON document containing metadata as specified by the flags.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/get_record_preview.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/get_record_preview.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def get_redo_record(self) -> str:
        """
        The `get_redo_record` method retrieves and removes a pending redo record.

        An empty value will be returned if there are no pending redo records.

        Use processRedoRecord() to process the result of this function.

        Once a redo record is retrieved, it is no longer tracked by Senzing.

        The redo record may be stored externally for later processing.

        See also countRedoRecords(), processRedoRecord()

        Returns:
            str: A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/get_redo_record.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/get_redo_record.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def get_stats(self) -> str:
        """
        The `get_stats` method gets and resets the internal engine workload statistics for the current
        operating system process.

        The output is helpful when interacting with Senzing support.

        Best practice to periodically log the results.

        Returns:
            str:  A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/get_stats.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/get_stats.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def get_virtual_entity_by_record_id(
        self,
        record_keys: List[Tuple[str, str]],
        flags: int = SzEngineFlags.SZ_VIRTUAL_ENTITY_DEFAULT_FLAGS,
    ) -> str:
        """
        The `get_virtual_entity_by_record_id` method describes how an entity would look if composed of a given
        set of records.

        Virtual entities do not have relationships.

        Args:
            record_keys (list(tuple(str, str))): The data source codes and record IDs identifying records to create the virtual entity from.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_VIRTUAL_ENTITY_DEFAULT_FLAGS.

        Returns:
            str:  A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/get_virtual_entity_by_record_id.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/get_virtual_entity_by_record_id.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def how_entity_by_entity_id(
        self,
        entity_id: int,
        flags: int = SzEngineFlags.SZ_HOW_ENTITY_DEFAULT_FLAGS,
    ) -> str:
        """
        The `how_entity_by_entity_id` method explains how an entity was constructed from its records.

        Args:
            entity_id (int): The unique identifier of an entity.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_HOW_ENTITY_DEFAULT_FLAGS.

        Returns:
            str: A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/how_entity_by_entity_id.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/how_entity_by_entity_id.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def prime_engine(self) -> None:
        """
        The `prime_engine` method pre-loads engine resources.

        Explicitly calling this method ensures the performance cost is incurred at a predictable time rather than
        unexpectedly with the first call requiring the resources.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/prime_engine.py
                :linenos:
                :language: python
        """

    @abstractmethod
    def process_redo_record(self, redo_record: str, flags: int = 0) -> str:
        """
        The `process_redo_record` method processes the provided redo record.

        This operation performs entity resolution.

        Calling processRedoRecord() has the potential to create more redo records in certain situations.

        See also getRedoRecord(), countRedoRecords()

        Args:
            redo_record (str): A redo record retrieved from get_redo_record.
            flags (int, optional): Flags used to control information returned. Defaults to 0.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/process_redo_record.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/process_redo_record.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def reevaluate_entity(self, entity_id: int, flags: int = SzEngineFlags.SZ_REEVALUATE_ENTITY_DEFAULT_FLAGS) -> str:
        """
        The `reevaluate_entity` method reevaluates an entity by entity ID.

        This operation performs entity resolution.

        If the entity is not found, then no changes are made.

        Args:
            entity_id (int): The unique identifier of an entity.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_REEVALUATE_ENTITY_DEFAULT_FLAGS.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/reevaluate_entity.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/reevaluate_entity.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def reevaluate_record(
        self, data_source_code: str, record_id: str, flags: int = SzEngineFlags.SZ_REEVALUATE_RECORD_DEFAULT_FLAGS
    ) -> str:
        """
        The `reevaluate_record` method reevaluates an entity by record ID.

        This operation performs entity resolution.

        If the record is not found, then no changes are made.

        Args:
            data_source_code (str): Identifies the provenance of the data.
            record_id (str): The unique identifier within the records of the same data source.
            flags (int, optional):  Flags used to control information returned. Defaults to SzEngineFlags.SZ_REEVALUATE_RECORD_DEFAULT_FLAGS.

        Returns:
            str: If flags are set to return the WITH_INFO response a JSON document containing the details, otherwise an empty string.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/reevaluate_record.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/reevaluate_record.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def search_by_attributes(
        self,
        attributes: str,
        flags: int = SzEngineFlags.SZ_SEARCH_BY_ATTRIBUTES_DEFAULT_FLAGS,
        search_profile: str = "",
    ) -> str:
        """
        The `search_by_attributes` method searches for entities that match or relate to the provided attributes.

        The default search profile is SEARCH.  Alternatively, INGEST may be used.

        Args:
            attributes (str): A JSON document with the attribute data to search for.
            flags (int, optional): _description_. Defaults to SzEngineFlags.SZ_SEARCH_BY_ATTRIBUTES_DEFAULT_FLAGS.
            search_profile (str): The name of a configured search profile. Defaults to SEARCH.

        Returns:
            str: A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/search_by_attributes.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/search_by_attributes.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def why_entities(
        self,
        entity_id_1: int,
        entity_id_2: int,
        flags: int = SzEngineFlags.SZ_WHY_ENTITIES_DEFAULT_FLAGS,
    ) -> str:
        """
        The `why_entities` method describes the ways two entities relate to each other.

        Args:
            entity_id_1 (int): The entity ID for the starting entity of the search path.
            entity_id_2 (int): The entity ID for the ending entity of the search path.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_WHY_ENTITIES_DEFAULT_FLAGS.

        Returns:
            str: A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/why_entities.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/why_entities.txt
                :linenos:
                :language: json
        """

    @abstractmethod
    def why_record_in_entity(
        self,
        data_source_code: str,
        record_id: str,
        flags: int = SzEngineFlags.SZ_WHY_RECORD_IN_ENTITY_DEFAULT_FLAGS,
    ) -> str:
        """
        The `why_record_in_entity` method describes the ways a record relates to the rest of its respective entity.

        Args:
            data_source_code (str): Identifies the provenance of the data.
            record_id (str): The unique identifier within the records of the same data source.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_WHY_RECORD_IN_ENTITY_DEFAULT_FLAGS.

        Returns:
            str: A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/why_record_in_entity.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/why_record_in_entity.txt
                    :linenos:
                    :language: json
        """

    @abstractmethod
    def why_records(
        self,
        data_source_code_1: str,
        record_id_1: str,
        data_source_code_2: str,
        record_id_2: str,
        flags: int = SzEngineFlags.SZ_WHY_RECORDS_DEFAULT_FLAGS,
    ) -> str:
        """
        The `why_records` method describes the ways two records relate to each other.

        Args:
            data_source_code_1 (str): Identifies the provenance of the data.
            record_id_1 (str): The unique identifier within the records of the same data source.
            data_source_code_2 (str): Identifies the provenance of the data.
            record_id_2 (str): The unique identifier within the records of the same data source.
            flags (int, optional): Flags used to control information returned. Defaults to SzEngineFlags.SZ_WHY_RECORDS_DEFAULT_FLAGS.

        Returns:
            str: A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/why_records.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/why_records.txt
                    :linenos:
                    :language: json
        """

    @abstractmethod
    def why_search(
        self,
        attributes: str,
        entity_id: int,
        flags: int = SzEngineFlags.SZ_WHY_SEARCH_DEFAULT_FLAGS,
        search_profile: str = "",
    ) -> str:
        """
        The `why_search` method describes the ways a set of search attributes relate to an entity.

        The default search profile is SEARCH.  Alternatively, INGEST may be used.

        Args:
            attributes (str): A JSON document with the attribute data to search for.
            entity_id (int): The identifier of the entity to retrieve.
            flags (int, optional): _description_. Defaults to SzEngineFlags.SZ_WHY_SEARCH_DEFAULT_FLAGS.
            search_profile (str): The name of a configured search profile. Defaults to SEARCH.

        Returns:
            str: A JSON document.

        Raises:
            SzError

        .. collapse:: Example:

            .. literalinclude:: ../../examples/szengine/why_search.py
                :linenos:
                :language: python

            **Output:**

            .. literalinclude:: ../../examples/szengine/why_search.txt
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
