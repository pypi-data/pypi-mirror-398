"""
szengineflags.py has constants that are used when calling Senzing functions.
"""

from enum import IntFlag
from typing import Dict, TypeVar

TSzEngineFlags = TypeVar("TSzEngineFlags", bound="SzEngineFlags")  # pylint: disable=C0103


# Metadata

__all__ = ["SzEngineFlags"]
__updated__ = "2025-08-11"


# -----------------------------------------------------------------------------
# SzEngineFlags class
# -----------------------------------------------------------------------------


class SzEngineFlags(IntFlag):
    """Engine Flags"""

    @classmethod
    def _members_dict(cls) -> Dict[str, int]:
        return {member.name: member.value for member in cls if member.name and not member.name.startswith("_")}

    # Constant for specifying no flags.

    SZ_NO_FLAGS = 0

    # Flags for including special data.

    SZ_INCLUDE_FEATURE_SCORES = 1 << 26
    SZ_INCLUDE_MATCH_KEY_DETAILS = 1 << 34

    # Flags for exporting entity data.

    SZ_EXPORT_INCLUDE_MULTI_RECORD_ENTITIES = 1 << 0
    SZ_EXPORT_INCLUDE_POSSIBLY_SAME = 1 << 1
    SZ_EXPORT_INCLUDE_POSSIBLY_RELATED = 1 << 2
    SZ_EXPORT_INCLUDE_NAME_ONLY = 1 << 3
    SZ_EXPORT_INCLUDE_DISCLOSED = 1 << 4
    SZ_EXPORT_INCLUDE_SINGLE_RECORD_ENTITIES = 1 << 5
    SZ_EXPORT_INCLUDE_ALL_ENTITIES = SZ_EXPORT_INCLUDE_MULTI_RECORD_ENTITIES | SZ_EXPORT_INCLUDE_SINGLE_RECORD_ENTITIES
    SZ_EXPORT_INCLUDE_ALL_HAVING_RELATIONSHIPS = (
        SZ_EXPORT_INCLUDE_POSSIBLY_SAME
        | SZ_EXPORT_INCLUDE_POSSIBLY_RELATED
        | SZ_EXPORT_INCLUDE_NAME_ONLY
        | SZ_EXPORT_INCLUDE_DISCLOSED
    )

    # Flags for outputting entity relation data.

    SZ_ENTITY_INCLUDE_POSSIBLY_SAME_RELATIONS = 1 << 6
    SZ_ENTITY_INCLUDE_POSSIBLY_RELATED_RELATIONS = 1 << 7
    SZ_ENTITY_INCLUDE_NAME_ONLY_RELATIONS = 1 << 8
    SZ_ENTITY_INCLUDE_DISCLOSED_RELATIONS = 1 << 9
    SZ_ENTITY_INCLUDE_ALL_RELATIONS = (
        SZ_ENTITY_INCLUDE_POSSIBLY_SAME_RELATIONS
        | SZ_ENTITY_INCLUDE_POSSIBLY_RELATED_RELATIONS
        | SZ_ENTITY_INCLUDE_NAME_ONLY_RELATIONS
        | SZ_ENTITY_INCLUDE_DISCLOSED_RELATIONS
    )

    # Flags for outputting entity feature data.

    SZ_ENTITY_INCLUDE_ALL_FEATURES = 1 << 10
    SZ_ENTITY_INCLUDE_REPRESENTATIVE_FEATURES = 1 << 11

    # Flags for getting extra information about an entity.

    SZ_ENTITY_INCLUDE_ENTITY_NAME = 1 << 12
    SZ_ENTITY_INCLUDE_RECORD_SUMMARY = 1 << 13
    SZ_ENTITY_INCLUDE_RECORD_TYPES = 1 << 28
    SZ_ENTITY_INCLUDE_RECORD_DATA = 1 << 14
    SZ_ENTITY_INCLUDE_RECORD_MATCHING_INFO = 1 << 15
    SZ_ENTITY_INCLUDE_RECORD_DATES = 1 << 39
    SZ_ENTITY_INCLUDE_RECORD_JSON_DATA = 1 << 16
    SZ_ENTITY_INCLUDE_RECORD_UNMAPPED_DATA = 1 << 31
    SZ_ENTITY_INCLUDE_RECORD_FEATURES = 1 << 18
    SZ_ENTITY_INCLUDE_RECORD_FEATURE_DETAILS = 1 << 35
    SZ_ENTITY_INCLUDE_RECORD_FEATURE_STATS = 1 << 36
    SZ_ENTITY_INCLUDE_RELATED_ENTITY_NAME = 1 << 19
    SZ_ENTITY_INCLUDE_RELATED_MATCHING_INFO = 1 << 20
    SZ_ENTITY_INCLUDE_RELATED_RECORD_SUMMARY = 1 << 21
    SZ_ENTITY_INCLUDE_RELATED_RECORD_TYPES = 1 << 29
    SZ_ENTITY_INCLUDE_RELATED_RECORD_DATA = 1 << 22

    # Flags for extra feature data.

    SZ_ENTITY_INCLUDE_INTERNAL_FEATURES = 1 << 23
    SZ_ENTITY_INCLUDE_FEATURE_STATS = 1 << 24

    # Flags for finding entity path data.

    SZ_FIND_PATH_STRICT_AVOID = 1 << 25
    SZ_FIND_PATH_INCLUDE_MATCHING_INFO = 1 << 30
    SZ_FIND_NETWORK_INCLUDE_MATCHING_INFO = 1 << 33

    # Flags for including search result feature scores.

    SZ_SEARCH_INCLUDE_STATS = 1 << 27

    # Flags for searching for entities.

    SZ_SEARCH_INCLUDE_RESOLVED = SZ_EXPORT_INCLUDE_MULTI_RECORD_ENTITIES
    SZ_SEARCH_INCLUDE_POSSIBLY_SAME = SZ_EXPORT_INCLUDE_POSSIBLY_SAME
    SZ_SEARCH_INCLUDE_POSSIBLY_RELATED = SZ_EXPORT_INCLUDE_POSSIBLY_RELATED
    SZ_SEARCH_INCLUDE_NAME_ONLY = SZ_EXPORT_INCLUDE_NAME_ONLY
    SZ_SEARCH_INCLUDE_ALL_ENTITIES = (
        SZ_SEARCH_INCLUDE_RESOLVED
        | SZ_SEARCH_INCLUDE_POSSIBLY_SAME
        | SZ_SEARCH_INCLUDE_POSSIBLY_RELATED
        | SZ_SEARCH_INCLUDE_NAME_ONLY
    )
    SZ_SEARCH_INCLUDE_ALL_CANDIDATES = 1 << 32
    SZ_SEARCH_INCLUDE_REQUEST = 1 << 37
    SZ_SEARCH_INCLUDE_REQUEST_DETAILS = 1 << 38

    # Recommended settings for various API functions.

    # The recommended default flag values for getting records.
    SZ_RECORD_DEFAULT_FLAGS = SZ_ENTITY_INCLUDE_RECORD_JSON_DATA

    # The recommended default flag values for basic entity output.
    SZ_ENTITY_CORE_FLAGS = (
        SZ_ENTITY_INCLUDE_REPRESENTATIVE_FEATURES
        | SZ_ENTITY_INCLUDE_ENTITY_NAME
        | SZ_ENTITY_INCLUDE_RECORD_SUMMARY
        | SZ_ENTITY_INCLUDE_RECORD_DATA
        | SZ_ENTITY_INCLUDE_RECORD_MATCHING_INFO
    )

    # The recommended default flag values for getting entities.
    SZ_ENTITY_DEFAULT_FLAGS = (
        SZ_ENTITY_CORE_FLAGS
        | SZ_ENTITY_INCLUDE_ALL_RELATIONS
        | SZ_ENTITY_INCLUDE_RELATED_ENTITY_NAME
        | SZ_ENTITY_INCLUDE_RELATED_RECORD_SUMMARY
        | SZ_ENTITY_INCLUDE_RELATED_MATCHING_INFO
    )

    # The recommended default flag values for a brief entity result.
    SZ_ENTITY_BRIEF_DEFAULT_FLAGS = (
        SZ_ENTITY_INCLUDE_RECORD_MATCHING_INFO
        | SZ_ENTITY_INCLUDE_ALL_RELATIONS
        | SZ_ENTITY_INCLUDE_RELATED_MATCHING_INFO
    )

    # The recommended default flag values for exporting entities.
    SZ_EXPORT_DEFAULT_FLAGS = SZ_EXPORT_INCLUDE_ALL_ENTITIES | SZ_ENTITY_DEFAULT_FLAGS

    # The recommended default flag values for finding entity paths.
    SZ_FIND_PATH_DEFAULT_FLAGS = (
        SZ_FIND_PATH_INCLUDE_MATCHING_INFO | SZ_ENTITY_INCLUDE_ENTITY_NAME | SZ_ENTITY_INCLUDE_RECORD_SUMMARY
    )
    SZ_FIND_NETWORK_DEFAULT_FLAGS = (
        SZ_FIND_NETWORK_INCLUDE_MATCHING_INFO | SZ_ENTITY_INCLUDE_ENTITY_NAME | SZ_ENTITY_INCLUDE_RECORD_SUMMARY
    )

    # The recommended default flag values for why-analysis on entities.
    SZ_WHY_ENTITIES_DEFAULT_FLAGS = SZ_INCLUDE_FEATURE_SCORES
    SZ_WHY_RECORDS_DEFAULT_FLAGS = SZ_INCLUDE_FEATURE_SCORES
    SZ_WHY_RECORD_IN_ENTITY_DEFAULT_FLAGS = SZ_INCLUDE_FEATURE_SCORES
    SZ_WHY_SEARCH_DEFAULT_FLAGS = (
        SZ_INCLUDE_FEATURE_SCORES | SZ_SEARCH_INCLUDE_REQUEST_DETAILS | SZ_SEARCH_INCLUDE_STATS
    )

    # The recommended default flag values for how-analysis on entities.
    SZ_HOW_ENTITY_DEFAULT_FLAGS = SZ_INCLUDE_FEATURE_SCORES

    # The recommended default flag values for virtual-entity-analysis on entities.
    SZ_VIRTUAL_ENTITY_DEFAULT_FLAGS = SZ_ENTITY_CORE_FLAGS

    # The recommended default flag values for adding records.
    SZ_ADD_RECORD_DEFAULT_FLAGS = SZ_NO_FLAGS

    # The recommended default flag values for deleting records.
    SZ_DELETE_RECORD_DEFAULT_FLAGS = SZ_NO_FLAGS

    # The recommended default flag values for preprocessing.
    SZ_RECORD_PREVIEW_DEFAULT_FLAGS = SZ_ENTITY_INCLUDE_RECORD_FEATURE_DETAILS

    # The recommended default flag values for redoing records.
    SZ_REDO_DEFAULT_FLAGS = SZ_NO_FLAGS

    # The recommended default flag values for reevaluating entities.
    SZ_REEVALUATE_RECORD_DEFAULT_FLAGS = SZ_NO_FLAGS
    SZ_REEVALUATE_ENTITY_DEFAULT_FLAGS = SZ_REEVALUATE_RECORD_DEFAULT_FLAGS

    # The recommended default flag values for finding interesting entities.
    SZ_FIND_INTERESTING_ENTITIES_DEFAULT_FLAGS = SZ_NO_FLAGS

    # The recommended settings for searching by attributes.

    # The recommended flag values for searching by attributes, returning all matching entities.
    SZ_SEARCH_BY_ATTRIBUTES_ALL = (
        SZ_SEARCH_INCLUDE_ALL_ENTITIES
        | SZ_ENTITY_INCLUDE_REPRESENTATIVE_FEATURES
        | SZ_ENTITY_INCLUDE_ENTITY_NAME
        | SZ_ENTITY_INCLUDE_RECORD_SUMMARY
        | SZ_INCLUDE_FEATURE_SCORES
        | SZ_SEARCH_INCLUDE_STATS
    )

    # The recommended flag values for searching by attributes, returning only strongly matching entities.
    SZ_SEARCH_BY_ATTRIBUTES_STRONG = (
        SZ_SEARCH_INCLUDE_RESOLVED
        | SZ_SEARCH_INCLUDE_POSSIBLY_SAME
        | SZ_ENTITY_INCLUDE_REPRESENTATIVE_FEATURES
        | SZ_ENTITY_INCLUDE_ENTITY_NAME
        | SZ_ENTITY_INCLUDE_RECORD_SUMMARY
        | SZ_INCLUDE_FEATURE_SCORES
        | SZ_SEARCH_INCLUDE_STATS
    )

    # Return minimal data with all matches.
    SZ_SEARCH_BY_ATTRIBUTES_MINIMAL_ALL = SZ_SEARCH_INCLUDE_ALL_ENTITIES | SZ_SEARCH_INCLUDE_STATS

    # Return minimal data with only the strongest matches.
    SZ_SEARCH_BY_ATTRIBUTES_MINIMAL_STRONG = (
        SZ_SEARCH_INCLUDE_RESOLVED | SZ_SEARCH_INCLUDE_POSSIBLY_SAME | SZ_SEARCH_INCLUDE_STATS
    )

    # The recommended default flag values for search-by-attributes.
    SZ_SEARCH_BY_ATTRIBUTES_DEFAULT_FLAGS = SZ_SEARCH_BY_ATTRIBUTES_ALL

    # Flag for returning (or not) with info responses.

    SZ_WITH_INFO = 1 << 62
    _SZ_WITHOUT_INFO = 0  # _SZ_WITHOUT_INFO isn't in the C API, will be used for future methods.
