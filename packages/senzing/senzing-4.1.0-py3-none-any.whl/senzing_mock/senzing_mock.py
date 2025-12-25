"""
szabstractfactory_Mock.py
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from senzing import (
    SzAbstractFactory,
    SzConfig,
    SzConfigManager,
    SzDiagnostic,
    SzEngine,
    SzEngineFlags,
    SzProduct,
)

# -----------------------------------------------------------------------------
# SzConfigMock class
# -----------------------------------------------------------------------------


class SzConfigMock(SzConfig):
    """
    SzConfig module access library.
    """

    # -------------------------------------------------------------------------
    # SzConfig methods
    # -------------------------------------------------------------------------

    def register_data_source(
        self,
        data_source_code: str,
    ) -> str:
        return ""

    def unregister_data_source(
        self,
        data_source_code: str,
    ) -> str:
        return ""

    def export(self) -> str:
        return ""

    def get_data_source_registry(self) -> str:
        return ""


# -----------------------------------------------------------------------------
# SzConfigManagerMock class
# -----------------------------------------------------------------------------


class SzConfigManagerMock(SzConfigManager):
    """
    SzConfigManager module access library.
    """

    # -------------------------------------------------------------------------
    # SzConfigManager methods
    # -------------------------------------------------------------------------

    def create_config_from_config_id(self, config_id: int) -> SzConfig:
        return SzConfigMock()

    def create_config_from_string(self, config_definition: str) -> SzConfig:
        return SzConfigMock()

    def create_config_from_template(self) -> SzConfig:
        return SzConfigMock()

    def get_config_registry(self) -> str:
        return ""

    def get_default_config_id(self) -> int:
        return 0

    def register_config(
        self,
        config_definition: Union[str, Dict[Any, Any]],
        config_comment: str,
    ) -> int:
        return 0

    def replace_default_config_id(
        self, current_default_config_id: int, new_default_config_id: int, **kwargs: Any
    ) -> None:
        """None"""

    def set_default_config(self, config_definition: str, config_comment: str) -> int:
        return 0

    def set_default_config_id(self, config_id: int) -> None:
        """None"""


# -----------------------------------------------------------------------------
# SzDiagnosticMock class
# -----------------------------------------------------------------------------


class SzDiagnosticMock(SzDiagnostic):
    """
    SzDiagnostic module access library.
    """

    # -------------------------------------------------------------------------
    # SzDiagnostic methods
    # -------------------------------------------------------------------------

    def check_repository_performance(self, seconds_to_run: int) -> str:
        return ""

    def get_repository_info(self) -> str:
        return ""

    def get_feature(self, feature_id: int) -> str:
        return ""

    def purge_repository(self) -> None:
        """None"""


# -----------------------------------------------------------------------------
# SzEngineMock class
# -----------------------------------------------------------------------------


class SzEngineMock(SzEngine):
    """
    SzEngine module access library.
    """

    # -------------------------------------------------------------------------
    # SzEngine methods
    # -------------------------------------------------------------------------

    def add_record(
        self,
        data_source_code: str,
        record_id: str,
        record_definition: str,
        flags: int = 0,
    ) -> str:
        return ""

    def close_export_report(self, export_handle: int) -> None:
        """None"""

    def count_redo_records(self) -> int:
        return 0

    def delete_record(
        self,
        data_source_code: str,
        record_id: str,
        flags: int = 0,
    ) -> str:
        return ""

    def export_csv_entity_report(
        self,
        csv_column_list: str,
        flags: int = SzEngineFlags.SZ_EXPORT_DEFAULT_FLAGS,
    ) -> int:
        return 0

    def export_json_entity_report(self, flags: int = SzEngineFlags.SZ_EXPORT_DEFAULT_FLAGS) -> int:
        return 0

    def fetch_next(self, export_handle: int) -> str:
        return ""

    def find_interesting_entities_by_entity_id(self, entity_id: int, flags: int = 0) -> str:
        return ""

    def find_interesting_entities_by_record_id(self, data_source_code: str, record_id: str, flags: int = 0) -> str:
        return ""

    def find_network_by_entity_id(
        self,
        entity_ids: List[int],
        max_degrees: int,
        build_out_degrees: int,
        build_out_max_entities: int,
        flags: int = SzEngineFlags.SZ_FIND_NETWORK_DEFAULT_FLAGS,
    ) -> str:
        return ""

    def find_network_by_record_id(
        self,
        record_keys: List[Tuple[str, str]],
        max_degrees: int,
        build_out_degrees: int,
        build_out_max_entities: int,
        flags: int = SzEngineFlags.SZ_FIND_NETWORK_DEFAULT_FLAGS,
    ) -> str:
        return ""

    def find_path_by_entity_id(
        self,
        start_entity_id: int,
        end_entity_id: int,
        max_degrees: int,
        avoid_entity_ids: Optional[List[int]] = None,
        required_data_sources: Optional[List[str]] = None,
        flags: int = SzEngineFlags.SZ_FIND_PATH_DEFAULT_FLAGS,
    ) -> str:
        return ""

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
        return ""

    def get_active_config_id(self) -> int:
        return 0

    def get_entity_by_entity_id(
        self,
        entity_id: int,
        flags: int = SzEngineFlags.SZ_ENTITY_DEFAULT_FLAGS,
    ) -> str:
        return ""

    def get_entity_by_record_id(
        self,
        data_source_code: str,
        record_id: str,
        flags: int = SzEngineFlags.SZ_ENTITY_DEFAULT_FLAGS,
    ) -> str:
        return ""

    def get_record(
        self,
        data_source_code: str,
        record_id: str,
        flags: int = SzEngineFlags.SZ_RECORD_DEFAULT_FLAGS,
    ) -> str:
        return ""

    def get_redo_record(self) -> str:
        return ""

    def get_stats(self) -> str:
        return ""

    def get_virtual_entity_by_record_id(
        self,
        record_keys: List[Tuple[str, str]],
        flags: int = SzEngineFlags.SZ_VIRTUAL_ENTITY_DEFAULT_FLAGS,
    ) -> str:
        return ""

    def how_entity_by_entity_id(
        self,
        entity_id: int,
        flags: int = SzEngineFlags.SZ_HOW_ENTITY_DEFAULT_FLAGS,
    ) -> str:
        return ""

    def get_record_preview(
        self,
        record_definition: str,
        flags: int = 0,
    ) -> str:
        return ""

    def prime_engine(self) -> None:
        """None"""

    def process_redo_record(self, redo_record: str, flags: int = 0) -> str:
        return ""

    def reevaluate_entity(self, entity_id: int, flags: int = 0) -> str:
        return ""

    def reevaluate_record(
        self,
        data_source_code: str,
        record_id: str,
        flags: int = 0,
    ) -> str:
        return ""

    def search_by_attributes(
        self,
        attributes: str,
        flags: int = SzEngineFlags.SZ_SEARCH_BY_ATTRIBUTES_DEFAULT_FLAGS,
        search_profile: str = "",
    ) -> str:
        return ""

    def why_entities(
        self,
        entity_id_1: int,
        entity_id_2: int,
        flags: int = SzEngineFlags.SZ_WHY_ENTITIES_DEFAULT_FLAGS,
    ) -> str:
        return ""

    def why_record_in_entity(
        self,
        data_source_code: str,
        record_id: str,
        flags: int = SzEngineFlags.SZ_WHY_RECORDS_DEFAULT_FLAGS,
    ) -> str:
        return ""

    def why_records(
        self,
        data_source_code_1: str,
        record_id_1: str,
        data_source_code_2: str,
        record_id_2: str,
        flags: int = SzEngineFlags.SZ_WHY_RECORDS_DEFAULT_FLAGS,
    ) -> str:
        return ""

    def why_search(
        self,
        attributes: str,
        entity_id: int,
        flags: int = SzEngineFlags.SZ_SEARCH_BY_ATTRIBUTES_DEFAULT_FLAGS,
        search_profile: str = "",
    ) -> str:
        return ""


# -----------------------------------------------------------------------------
# SzProductMock class
# -----------------------------------------------------------------------------


class SzProductMock(SzProduct):
    """
    SzProduct module access library.
    """

    # -------------------------------------------------------------------------
    # SzProduct methods
    # -------------------------------------------------------------------------

    def get_license(self) -> str:
        return ""

    def get_version(self) -> str:
        return ""


# -----------------------------------------------------------------------------
# SzAbstractFactoryMock class
# -----------------------------------------------------------------------------


class SzAbstractFactoryMock(SzAbstractFactory):
    """
    SzDiagnostic module access library.
    """

    # -------------------------------------------------------------------------
    # SzAbstractFactory methods
    # -------------------------------------------------------------------------

    def create_configmanager(self, **kwargs: Any) -> SzConfigManager:
        _ = kwargs
        return SzConfigManagerMock()

    def create_diagnostic(self, **kwargs: Any) -> SzDiagnostic:
        _ = kwargs
        return SzDiagnosticMock()

    def create_engine(self, **kwargs: Any) -> SzEngine:
        _ = kwargs
        return SzEngineMock()

    def create_product(self, **kwargs: Any) -> SzProduct:
        _ = kwargs
        return SzProductMock()

    def destroy(self, **kwargs: Any) -> None:
        _ = kwargs

    def reinitialize(self, config_id: int, **kwargs: Any) -> None:
        _ = kwargs


# -----------------------------------------------------------------------------
# SzAbstractFactoryMock instance
# -----------------------------------------------------------------------------

sz_abstract_factory = SzAbstractFactoryMock()
sz_config = SzConfigMock()
sz_configmanager = SzConfigManagerMock()
sz_diagnostic = SzDiagnosticMock()
sz_engine = SzEngineMock()
sz_product = SzProductMock()
