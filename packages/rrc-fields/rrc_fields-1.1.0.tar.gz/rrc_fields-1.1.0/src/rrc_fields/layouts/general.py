from .lookups import (
    DISTRICT_CODE_LOOKUP,
    FIELD_CLASS_LOOKUP,
    FORMATION_COMPOSITION_LOOKUP,
    FOUR_MONTH_TEST_EXCPT_LOOKUP,
    HYDROGEN_SULFIDE_CODE_LOOKUP,
    GAS_OIL_RATIO_CODE_LOOKUP,
    NET_GOR_RULE_CODE_LOOKUP
)

FLDROOT_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_DISTRICT', 'start': 2, 'length': 2, 'type': 'string', 'lookup': DISTRICT_CODE_LOOKUP},
    {'name': 'FL_NUMBER', 'start': 4, 'length': 8, 'type': 'zoned'},
    # Redefines FL_NUMBER:
    # {'name': 'FL_FIELD_NUMBER', 'start': 4, 'length': 5, 'type': 'zoned'},
    # {'name': 'FL_RESERVOIR_NUMBER', 'start': 9, 'length': 3, 'type': 'zoned'},
    {'name': 'FL_NAME', 'start': 12, 'length': 32, 'type': 'string'},
    {'name': 'FL_FIELD_CLASS', 'start': 44, 'length': 1, 'type': 'string', 'lookup': FIELD_CLASS_LOOKUP},
    {'name': 'FL_RESERVOIR_NAME', 'start': 45, 'length': 30, 'type': 'string'},
    {'name': 'FL_FORMATION_COMPOSITION', 'start': 75, 'length': 2, 'type': 'string', 'lookup': FORMATION_COMPOSITION_LOOKUP},
    # Filler 5 bytes at 77
    {'name': 'FL_4_MONTH_TEST_EXCPT', 'start': 82, 'length': 1, 'type': 'string', 'lookup': FOUR_MONTH_TEST_EXCPT_LOOKUP},
    # Filler 1 byte at 83
    {'name': 'FL_HYDROGEN_SULFIDE_CD', 'start': 84, 'length': 1, 'type': 'string', 'lookup': HYDROGEN_SULFIDE_CODE_LOOKUP},
    {'name': 'FL_GAS_OIL_RATIO_CODE', 'start': 85, 'length': 1, 'type': 'string', 'lookup': GAS_OIL_RATIO_CODE_LOOKUP},
    {'name': 'FL_GAS_OIL_RATIO_OR_LIMIT', 'start': 86, 'length': 5, 'type': 'zoned'},
    {'name': 'FL_NET_GOR_RULE_CODE', 'start': 91, 'length': 1, 'type': 'string', 'lookup': NET_GOR_RULE_CODE_LOOKUP},
    {'name': 'FL_NET_GOR_RATIO_OR_LIMIT', 'start': 92, 'length': 5, 'type': 'zoned'},
    {'name': 'FL_OIL_DISC_WELL_GRAVITY', 'start': 97, 'length': 3, 'type': 'zoned', 'scale': 1},
    {'name': 'FL_ASSOC_OIL_FIELD_NUMBER', 'start': 100, 'length': 8, 'type': 'zoned'},
    {'name': 'FL_DISCOV_PERMIT_NUM', 'start': 108, 'length': 7, 'type': 'zoned'},
    {'name': 'FL_NEW_FIELD_DISCOV_FLAG', 'start': 115, 'length': 1, 'type': 'string'},
    {'name': 'FL_NFD_SYS_CC', 'start': 116, 'length': 2, 'type': 'zoned'},
    {'name': 'FL_NFD_SYS_YR', 'start': 118, 'length': 2, 'type': 'zoned'},
    {'name': 'FL_NFD_SYS_MO', 'start': 120, 'length': 2, 'type': 'zoned'},
    {'name': 'FL_NFD_SYS_DA', 'start': 122, 'length': 2, 'type': 'zoned'},
    {'name': 'FL_RRC_RETURNED_TO_PR_FLAG', 'start': 124, 'length': 1, 'type': 'string'},
    {'name': 'FL_RRC_RET_TO_PR_CENTURY', 'start': 125, 'length': 2, 'type': 'zoned'},
    {'name': 'FL_RRC_RET_TO_PR_YEAR', 'start': 127, 'length': 2, 'type': 'zoned'},
    {'name': 'FL_RRC_RET_TO_PR_MONTH', 'start': 129, 'length': 2, 'type': 'zoned'},
    {'name': 'FL_SET_TO_AOF_BY_ORDER_FLAG', 'start': 131, 'length': 1, 'type': 'string'},
    {'name': 'FL_SET_TO_AOF_BY_ORDER_CENTURY', 'start': 132, 'length': 2, 'type': 'zoned'},
    {'name': 'FL_SET_TO_AOF_BY_ORDER_YEAR', 'start': 134, 'length': 2, 'type': 'zoned'},
    {'name': 'FL_SET_TO_AOF_BY-ORDER_MONTH', 'start': 136, 'length': 2, 'type': 'zoned'},
    {'name': 'FL_MANUAL_REVIEW_FLAG', 'start': 138, 'length': 1, 'type': 'string'},
    # Filler 3 bytes at 139
]

FLDMAP_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_MAP_NUMBER_INDEX', 'start': 2, 'length': 6, 'type': 'string'}, # PIC X(6)
    {'name': 'FL_MAP_COUNTY_CODE_1', 'start': 8, 'length': 3, 'type': 'string'}, # PIC X(3)
    {'name': 'FL_MAP_COUNTY_CODE_2', 'start': 11, 'length': 3, 'type': 'string'},
    {'name': 'FL_MAP_COUNTY_CODE_3', 'start': 14, 'length': 3, 'type': 'string'},
    {'name': 'FL_MAP_COUNTY_CODE_4', 'start': 17, 'length': 3, 'type': 'string'},
    {'name': 'FL_MAP_COUNTY_CODE_5', 'start': 20, 'length': 3, 'type': 'string'},
    {'name': 'FL_MAP_COUNTY_CODE_6', 'start': 23, 'length': 3, 'type': 'string'},
]
