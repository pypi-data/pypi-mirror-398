from .lookups import (
    DISTRICT_CODE_LOOKUP, 
    ALLOCATION_FACTOR_LOOKUP,
    GAS_TYPE_FIELD_CODE_LOOKUP,
    GAS_LIMITED_PROD_ALLOWABLE_LOOKUP,
    GAS_BALANCE_RULE_CODE_LOOKUP,
    GAS_NO_PAST_PROD_FLAG_LOOKUP,
    GAS_NO_HIGHEST_DAILY_FLAG_LOOKUP,
    GAS_LIMIT_ALLOW_HEARING_FLAG_LOOKUP,
    GAS_CAPABILITY_REVIEW_FLAG_LOOKUP,
    ELIGIBLE_FOR_250_SPEC_FLAG_LOOKUP,
    SIWH_EXCEPTION_FLAG_LOOKUP,
    GAS_FIELD_TYPE_LOOKUP,
    GAS_TEST_FREQUENCY_LOOKUP,
    G10_REQUIREMENT_LOOKUP,
    GAS_EXEMPT_MIN_GOR_LOOKUP,
    OFFSHORE_CODE_LOOKUP,
    SALT_DOME_EXEMPTION_LOOKUP,
    COUNTY_REGULAR_EXEMPTION_LOOKUP,
    GAS_CONSOLIDATED_FIELD_FLAG_LOOKUP
)

GASSEG_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_GASSEG_KEY', 'start': 2, 'length': 1, 'type': 'string'},
    {'name': 'FL_GAS_DISC_CENTURY', 'start': 3, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_DISC_YEAR', 'start': 5, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_DISC_MONTH', 'start': 7, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_DISC_DAY', 'start': 9, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_DISC_COUNTY_CODE', 'start': 11, 'length': 3, 'type': 'string'},
    {'name': 'FL_GAS_PERF_1ST_WELL', 'start': 14, 'length': 5, 'type': 'string'},
    {'name': 'FL_TYPE_FIELD_CODE', 'start': 19, 'length': 1, 'type': 'string', 'lookup': GAS_FIELD_TYPE_LOOKUP},
    # Filler 8 bytes at 20
    {'name': 'FL_GAS_TESTING_COUNTY', 'start': 28, 'length': 3, 'type': 'string'},
    {'name': 'FL_GAS_TEST_FREQUENCY', 'start': 31, 'length': 1, 'type': 'string', 'lookup': GAS_TEST_FREQUENCY_LOOKUP},
    {'name': 'FL_GAS_PRI_ALTER_TEST_MONTH', 'start': 32, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_SEC_ALTER_TEST_MONTH', 'start': 34, 'length': 2, 'type': 'string'},
    {'name': 'FL_PRI_TEST_MON_G10_REQUIRE', 'start': 36, 'length': 1, 'type': 'string', 'lookup': G10_REQUIREMENT_LOOKUP},
    {'name': 'FL_SEC_TEST_MON_G10_REQUIRE', 'start': 37, 'length': 1, 'type': 'string', 'lookup': G10_REQUIREMENT_LOOKUP},
    # Filler 2 bytes at 38
    {'name': 'FL_GAS_COMMINGLING_COUNTER', 'start': 40, 'length': 5, 'type': 'string'},
    {'name': 'FL_GAS_EXEMPT_MINIMUM_GOR', 'start': 45, 'length': 1, 'type': 'string', 'lookup': GAS_EXEMPT_MIN_GOR_LOOKUP},
    {'name': 'FL_OFFSHORE_CODE', 'start': 46, 'length': 2, 'type': 'string', 'lookup': OFFSHORE_CODE_LOOKUP},
    # Filler 1 byte at 48 (offset 49 in doc means start 48 0-indexed)
    {'name': 'FL_CUM_GAS_PRODUCTION_TO_CONV', 'start': 49, 'length': 7, 'type': 'packed', 'scale': 0}, # 13 digits = 7 bytes
    {'name': 'FL_CUM_COND_PRODUCTION_TO_CONV', 'start': 56, 'length': 6, 'type': 'packed', 'scale': 0}, # 11 digits = 6 bytes
    {'name': 'FL_CUM_GAS_ALLOWABLE_TO_CONV', 'start': 62, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_CUM_LIQ_ALLOWABLE_TO_CONV', 'start': 69, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OFF_FILE_CUM_GAS_ALLOWABLE', 'start': 76, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OFF_FILE_CUM_LIQ_ALLOWABLE', 'start': 83, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OFF_FILE_CUM_GAS_PROD', 'start': 90, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OFF_FILE_CUM_COND_PROD', 'start': 97, 'length': 6, 'type': 'packed', 'scale': 0},
    {'name': 'FL_ON_FILE_CUM_GAS_ALLOWABLE', 'start': 103, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_ON_FILE_CUM_LIQ_ALLOWABLE', 'start': 110, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_ON_FILE_CUM_GAS_PROD', 'start': 117, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_ON_FILE_CUM_COND_PROD', 'start': 124, 'length': 6, 'type': 'packed', 'scale': 0},
    {'name': 'FL_YR_TO_DT_CUM_GAS_ALLOWABLE', 'start': 130, 'length': 6, 'type': 'packed', 'scale': 0},
    {'name': 'FL_YR_TO_DT_CUM_LIQ_ALLOWABLE', 'start': 136, 'length': 6, 'type': 'packed', 'scale': 0},
    {'name': 'FL_YR_TO_DT_CUM_GAS_PROD', 'start': 142, 'length': 6, 'type': 'packed', 'scale': 0},
    {'name': 'FL_YR_TO_DT_CUM_COND_PROD', 'start': 148, 'length': 6, 'type': 'packed', 'scale': 0},
    {'name': 'FL_SALT_DOME_EXEMPTION', 'start': 154, 'length': 1, 'type': 'string', 'lookup': SALT_DOME_EXEMPTION_LOOKUP},
    {'name': 'FL_COUNTY_REGULAR_EXEMPTION', 'start': 155, 'length': 1, 'type': 'string', 'lookup': COUNTY_REGULAR_EXEMPTION_LOOKUP},
    {'name': 'FL_LEDGER_MONTH', 'start': 156, 'length': 2, 'type': 'string'},
    {'name': 'FL_NEW_GAS_FLD_APPR_CENTURY', 'start': 158, 'length': 2, 'type': 'string'},
    {'name': 'FL_NEW_GAS_FLD_APPR_YEAR', 'start': 160, 'length': 2, 'type': 'string'},
    {'name': 'FL_NEW_GAS_FLD_APPR_MONTH', 'start': 162, 'length': 2, 'type': 'string'},
    {'name': 'FL_NEW_GAS_FLD_APPR_DAY', 'start': 164, 'length': 2, 'type': 'string'},
    {'name': 'FL_CUM_PROD_PRIOR_1970', 'start': 166, 'length': 7, 'type': 'packed', 'scale': 0}, # 12 digits -> 7 bytes? Usually 12 digits fits in 7 bytes (13 nibbles + sign)
    {'name': 'FL_GAS_SCHED_START_CENTURY', 'start': 173, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_SCHED_START_YEAR', 'start': 175, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_SCHED_START_MONTH', 'start': 177, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_SCHED_START_DAY', 'start': 179, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_CONSOLIDATED_FIELD_FLAG', 'start': 181, 'length': 1, 'type': 'string', 'lookup': GAS_CONSOLIDATED_FIELD_FLAG_LOOKUP},
    {'name': 'FL_GAS_CORRELATIVE_INTER_FROM', 'start': 182, 'length': 5, 'type': 'string'},
    {'name': 'FL_GAS_CORRELATIVE_INTER_TO', 'start': 187, 'length': 5, 'type': 'string'},
]

GASCYCLE_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_CYCLE_KEY', 'start': 2, 'length': 4, 'type': 'string'}, # PIC 9(04) Key
    {'name': 'FL_GAS_TYPE_FIELD_CODE', 'start': 6, 'length': 2, 'type': 'string', 'lookup': GAS_TYPE_FIELD_CODE_LOOKUP},
    {'name': 'FL_COUNTY_REGULAR_INDICATOR', 'start': 8, 'length': 1, 'type': 'string'},
    {'name': 'FL_GAS_LIMITED_PROD_ALLOWABLE', 'start': 9, 'length': 2, 'type': 'string', 'lookup': GAS_LIMITED_PROD_ALLOWABLE_LOOKUP},
    {'name': 'FL_GAS_BALANCE_RULE_CODE', 'start': 11, 'length': 1, 'type': 'string', 'lookup': GAS_BALANCE_RULE_CODE_LOOKUP},
    {'name': 'FL_GAS_NO_PAST_PRODUCTION_FLAG', 'start': 12, 'length': 1, 'type': 'string', 'lookup': GAS_NO_PAST_PROD_FLAG_LOOKUP},
    {'name': 'FL_GAS_NO_HIGHEST_DAILY_FLAG', 'start': 13, 'length': 1, 'type': 'string', 'lookup': GAS_NO_HIGHEST_DAILY_FLAG_LOOKUP},
    {'name': 'FL_GAS_HIGHEST_DAILY_CYCLES', 'start': 14, 'length': 1, 'type': 'string'}, # PIC 9(1)
    {'name': 'FL_GAS_EXCEPT_HIGH_DAY_AMOUNT', 'start': 15, 'length': 5, 'type': 'packed', 'scale': 0}, # S9(9) COMP-3
    {'name': 'FL_GAS_PAST_PRODUCTION_CYCLES', 'start': 20, 'length': 1, 'type': 'string'},
    {'name': 'FL_GAS_EXCEPT_PAST_PROD_AMOUNT', 'start': 21, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_GAS_WELLS_WITH_ALLOWABLES', 'start': 26, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_GAS_SCHEDULE_COLUMN_HDG_CD', 'start': 31, 'length': 1, 'type': 'string'},
    {'name': 'FL_GAS_LIMIT_ALLOW_HEARING_FLG', 'start': 32, 'length': 1, 'type': 'string', 'lookup': GAS_LIMIT_ALLOW_HEARING_FLAG_LOOKUP},
    {'name': 'FL_GAS_CAPABILITY_REVIEW_FLAG', 'start': 33, 'length': 1, 'type': 'string', 'lookup': GAS_CAPABILITY_REVIEW_FLAG_LOOKUP},
    {'name': 'FL_ELIGIBLE_FOR_250_SPEC_FLAG', 'start': 34, 'length': 1, 'type': 'string', 'lookup': ELIGIBLE_FOR_250_SPEC_FLAG_LOOKUP},
    {'name': 'FL_SIWH_EXCEPTION_FLAG', 'start': 36, 'length': 1, 'type': 'string', 'lookup': SIWH_EXCEPTION_FLAG_LOOKUP},
]

GSFLDRUL_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_RULE_EFFECTIVE_KEY', 'start': 2, 'length': 8, 'type': 'zoned', 'scale': 0}, # PIC 9(8)
    {'name': 'FL_GAS_PRORATION_EFF_DATE', 'start': 10, 'length': 8, 'type': 'zoned', 'scale': 0}, # CCYYMMDD
    {'name': 'FL_GAS_PRORATION_SUSPEND_DATE', 'start': 18, 'length': 8, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_RULES_RESCINDED_DATE', 'start': 26, 'length': 8, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_DOCKET_SUFFIX', 'start': 34, 'length': 3, 'type': 'string'},
    {'name': 'FL_GAS_SPACING_TO_LEASE_LINE', 'start': 37, 'length': 4, 'type': 'zoned', 'scale': 0}, # PIC 9(04)
    {'name': 'FL_GAS_SPACING_TO_WELL', 'start': 41, 'length': 4, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_INJECTION_CREDIT', 'start': 45, 'length': 1, 'type': 'string'},
    {'name': 'FL_GAS_ACRES_PER-UNIT', 'start': 46, 'length': 6, 'type': 'zoned', 'scale': 2}, # PIC 9(04)V99
    {'name': 'FL_GAS_TOLERANCE_ACRES', 'start': 52, 'length': 5, 'type': 'zoned', 'scale': 2}, # PIC 9(03)V99
    {'name': 'FL_GAS_CASING_CODE', 'start': 57, 'length': 1, 'type': 'string', 'lookup': {'F': 'FIELD RULES', 'W': 'TDWR'}},
    {'name': 'FL_GAS_CASING_DEPTH', 'start': 58, 'length': 5, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_CASING_REMARKS', 'start': 63, 'length': 32, 'type': 'string'},
    {'name': 'FL_GAS_DIAGONAL_CODE', 'start': 95, 'length': 2, 'type': 'string', 'lookup': {'CC': 'CORNER-TO-CORNER', 'WC': 'WELL-TO-CORNER'}},
    {'name': 'FL_GAS_DIAGONAL', 'start': 97, 'length': 5, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_DIAGONAL_REMARKS', 'start': 102, 'length': 21, 'type': 'string'},
    {'name': 'FL_GAS_FIELD_ALLOW_TOLERANCE', 'start': 123, 'length': 3, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_FIELD_TRANSFER_ALLOW', 'start': 126, 'length': 1, 'type': 'string'},
    {'name': 'FL_GAS_ALLOWABLE_BASIS', 'start': 127, 'length': 1, 'type': 'string'},
    {'name': 'FL_GAS_NO_MONTHS_AVERAGED', 'start': 128, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_FIELD_TEXT', 'start': 130, 'length': 60, 'type': 'string'},
    {'name': 'FL_GAS_OLD_ALLOCATION_CODE', 'start': 190, 'length': 1, 'type': 'string'},
    {'name': 'FL_GAS_CLASS_PENDING_CODE', 'start': 191, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_DOCKET_NUMBER', 'start': 193, 'length': 10, 'type': 'string'},
    {'name': 'FL_GAS_RULES_NOT_RELIABLE_FLAG', 'start': 203, 'length': 1, 'type': 'string'},
]

GASAFORM_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_ALLOW_PERCENT_FACTR', 'start': 2, 'length': 3, 'type': 'zoned', 'scale': 2}, # 9V99
    {'name': 'FL_GAS_ALLOCATION_FCTR_CD', 'start': 5, 'length': 2, 'type': 'string', 'lookup': ALLOCATION_FACTOR_LOOKUP},
]

GASRMRKS_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_REMARK_NUMBER', 'start': 2, 'length': 3, 'type': 'zoned', 'scale': 0}, # PIC 9(03)
    {'name': 'FL_GAS_REMARK_LINE_NO', 'start': 5, 'length': 3, 'type': 'zoned', 'scale': 0}, # PIC 9(03)
    {'name': 'FL_GAS_PRINT_ANNUAL_FLAG', 'start': 8, 'length': 1, 'type': 'string'},
    {'name': 'FL_GAS_PRINT_LEDGER_FLAG', 'start': 9, 'length': 1, 'type': 'string'},
    {'name': 'FL_GAS_PRINT_SCHEDULE_FLAG', 'start': 10, 'length': 1, 'type': 'string'},
    {'name': 'FL_GAS_PRINT_ON_LINE_FLAG', 'start': 11, 'length': 1, 'type': 'string'},
    {'name': 'FL_GAS_PRINT_ASHEET_FLAG', 'start': 12, 'length': 1, 'type': 'string'},
    {'name': 'FL_GAS_REMARK_DATE_CC', 'start': 13, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_REMARK_DATE_YY', 'start': 15, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_REMARK_DATE_MM', 'start': 17, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_REMARK_DATE_DD', 'start': 19, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_REMARK_TEXT', 'start': 21, 'length': 66, 'type': 'string'},
]

GSCOUNTY_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_COUNTY_CODE', 'start': 2, 'length': 3, 'type': 'zoned', 'scale': 0}, # PIC 9(03)
]

GASAFACT_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_FACTOR_CYCLE_KEY', 'start': 2, 'length': 4, 'type': 'zoned', 'scale': 0}, # PIC 9(04)
    # Factor 1
    {'name': 'FL_FACTOR_CODE_1', 'start': 6, 'length': 2, 'type': 'string', 'lookup': ALLOCATION_FACTOR_LOOKUP},
    {'name': 'FL_GAS_ALLOCATION_FACTOR_1', 'start': 8, 'length': 8, 'type': 'packed', 'scale': 7}, # S9(8)V9(7) COMP-3
    # Factor 2
    {'name': 'FL_FACTOR_CODE_2', 'start': 16, 'length': 2, 'type': 'string', 'lookup': ALLOCATION_FACTOR_LOOKUP},
    {'name': 'FL_GAS_ALLOCATION_FACTOR_2', 'start': 18, 'length': 8, 'type': 'packed', 'scale': 7},
    # Factor 3
    {'name': 'FL_FACTOR_CODE_3', 'start': 26, 'length': 2, 'type': 'string', 'lookup': ALLOCATION_FACTOR_LOOKUP},
    {'name': 'FL_GAS_ALLOCATION_FACTOR_3', 'start': 28, 'length': 8, 'type': 'packed', 'scale': 7},
    # Factor 4
    {'name': 'FL_FACTOR_CODE_4', 'start': 36, 'length': 2, 'type': 'string', 'lookup': ALLOCATION_FACTOR_LOOKUP},
    {'name': 'FL_GAS_ALLOCATION_FACTOR_4', 'start': 38, 'length': 8, 'type': 'packed', 'scale': 7},
    # Factor 5
    {'name': 'FL_FACTOR_CODE_5', 'start': 46, 'length': 2, 'type': 'string', 'lookup': ALLOCATION_FACTOR_LOOKUP},
    {'name': 'FL_GAS_ALLOCATION_FACTOR_5', 'start': 48, 'length': 8, 'type': 'packed', 'scale': 7},
    
    {'name': 'FL_ZERO_STAR_CODE', 'start': 56, 'length': 1, 'type': 'string'},
]

ASSOCGAS_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_ASSOC_GAS_FIELD_DIST', 'start': 2, 'length': 2, 'type': 'string', 'lookup': DISTRICT_CODE_LOOKUP}, # PIC 99
    {'name': 'FL_ASSOC_GAS_FIELD_NUMBER', 'start': 4, 'length': 8, 'type': 'zoned', 'scale': 0}, # PIC 9(8)
]

GSOPTRUL_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_OPT_KEY', 'start': 2, 'length': 2, 'type': 'zoned', 'scale': 0}, # PIC 9(02)
    {'name': 'FL_GAS_OPT_SPACE_TO_LEASE_LINE', 'start': 4, 'length': 4, 'type': 'zoned', 'scale': 0}, # PIC 9(04)
    {'name': 'FL_GAS_OPT_SPACE_TO_WELL', 'start': 8, 'length': 4, 'type': 'zoned', 'scale': 0}, # PIC 9(04)
    {'name': 'FL_GAS_OPT_ACRES_PER_UNIT', 'start': 12, 'length': 6, 'type': 'zoned', 'scale': 2}, # PIC 9(04)V99
    {'name': 'FL_GAS_OPT_TOLERANCE_ACRES', 'start': 18, 'length': 5, 'type': 'zoned', 'scale': 2}, # PIC 9(03)V99
    {'name': 'FL_GAS_OPT_DIAGONAL_CODE', 'start': 23, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_OPT_DIAGONAL_FEET', 'start': 25, 'length': 5, 'type': 'zoned', 'scale': 0}, # PIC 9(05)
    {'name': 'FL_GAS_OPT_FIELD_TEXT', 'start': 30, 'length': 47, 'type': 'string'},
]
