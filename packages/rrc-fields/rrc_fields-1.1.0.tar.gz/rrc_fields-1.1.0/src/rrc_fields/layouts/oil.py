from .lookups import (
    OIL_ALLOCATION_FACTOR_LOOKUP,
    ALLOCATION_FACTOR_LOOKUP,
    OFFSHORE_CODE_LOOKUP,
    OIL_CONSOLIDATED_FIELD_FLAG_LOOKUP
)

OILSEG_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_OILSEG_KEY', 'start': 2, 'length': 1, 'type': 'string'},
    {'name': 'FL_OIL_DISC_DATE_1ST_WELL', 'start': 3, 'length': 8, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_DISC_CENTURY', 'start': 3, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_DISC_YEAR', 'start': 5, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_DISC_MONTH', 'start': 7, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_DISC_DAY', 'start': 9, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_DISC_COUNTY_CODE', 'start': 11, 'length': 3, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_DEPTH_1ST_WELL', 'start': 14, 'length': 5, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_TESTING_COUNTY', 'start': 19, 'length': 3, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_1ST_ALTER_TEST_MONTH', 'start': 22, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_2ND_ALTER_TEST_MONTH', 'start': 24, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_OFFSHORE_CODE', 'start': 26, 'length': 2, 'type': 'string', 'lookup': OFFSHORE_CODE_LOOKUP},
    {'name': 'FL_OIL_SCHEDULE_COLUMN_HDG_CD', 'start': 28, 'length': 1, 'type': 'string'},
    
    # 7-byte Packed Decimals start at 29 (Pos 30)
    {'name': 'FL_CUM_OIL_PRODUCTION_TO_CONV', 'start': 29, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_CUM_CSHD_PRODUCTION_TO_CONV', 'start': 36, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_CUM_OIL_ALLOWABLE_TO_CONV', 'start': 43, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_CUM_CSHD_ALLOWABLE_TO_CONV', 'start': 50, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OFF_FILE_CUM_OIL_ALLOWABLE', 'start': 57, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OFF_FILE_CUM_CSHD_ALLOWABLE', 'start': 64, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OFF_FILE_CUM_OIL_PROD', 'start': 71, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OFF_FILE_CUM_CSHD_PROD', 'start': 78, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_ON_FILE_CUM_OIL_ALLOWABLE', 'start': 85, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_ON_FILE_CUM_CSHD_ALLOWABLE', 'start': 92, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_ON_FILE_CUM_OIL_PROD', 'start': 99, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_ON_FILE_CUM_CSHD_PROD', 'start': 106, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_YR_TO_DT_CUM_OIL_ALLOWABLE', 'start': 113, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_YR_TO_DT_CUM_CSHD_ALLOWABLE', 'start': 120, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_YR_TO_DT_CUM_OIL_PROD', 'start': 127, 'length': 7, 'type': 'packed', 'scale': 0},
    {'name': 'FL_YR_TO_DT_CUM_CSHD_PROD', 'start': 134, 'length': 7, 'type': 'packed', 'scale': 0},
    
    {'name': 'FL_OIL_LEDGER_MONTH', 'start': 141, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_SCHEDULE_LINES_COUNTER', 'start': 143, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_ANNUAL_LINES_COUNTER', 'start': 145, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_ORIGINAL_OIL_IN_PLACE', 'start': 147, 'length': 8, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_FLD_EB_EXEMPT_FLAG', 'start': 155, 'length': 1, 'type': 'string'},
    
    {'name': 'FL_OIL_SCHEDULE_START_DATE', 'start': 156, 'length': 8, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_SCHED_START_CENTURY', 'start': 156, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_SCHED_START_YEAR', 'start': 158, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_SCHED_START_MONTH', 'start': 160, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_SCHED_START_DAY', 'start': 162, 'length': 2, 'type': 'zoned', 'scale': 0},

    {'name': 'FL_NEW_FLD_APPRVL_CCYRMODA', 'start': 164, 'length': 8, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_NEW_FLD_APPRVL_CC', 'start': 164, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_NEW_FLD_APPRVL_YR', 'start': 166, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_NEW_FLD_APPRVL_MO', 'start': 168, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_NEW_FLD_APPRVL_DA', 'start': 170, 'length': 2, 'type': 'zoned', 'scale': 0},

    {'name': 'FL_OIL_CONSOLIDATED_FIELD_FLAG', 'start': 172, 'length': 1, 'type': 'string', 'lookup': OIL_CONSOLIDATED_FIELD_FLAG_LOOKUP},
]

OILCYCLE_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_OIL_CYCLE_KEY', 'start': 2, 'length': 4, 'type': 'zoned', 'scale': 0}, # PIC 9(04)
    {'name': 'FL_OIL_TYPE_FIELD_CODE', 'start': 6, 'length': 1, 'type': 'string'},
    {'name': 'FL_YARDSTICK', 'start': 7, 'length': 1, 'type': 'string'},
    {'name': 'FL_REGULAR_ALLOW_CALC_FLAG', 'start': 8, 'length': 1, 'type': 'string'},
    {'name': 'FL_OIL_TOP_ALLOWABLE_CD', 'start': 9, 'length': 1, 'type': 'string'},
    {'name': 'FL_OIL_TOP_ALLOWABLE_AMT', 'start': 10, 'length': 4, 'type': 'packed', 'scale': 0}, # PIC S9(06) COMP-3 (4 bytes)
    {'name': 'FL_OIL_RES_MER_AMOUNT', 'start': 14, 'length': 4, 'type': 'packed', 'scale': 0},   # PIC S9(06) COMP-3
    {'name': 'FL_OIL_COUNTY_REGULAR_FLAG', 'start': 18, 'length': 1, 'type': 'string'},
]

OLFLDRUL_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_OIL_RULE_EFFECTIVE_KEY', 'start': 2, 'length': 8, 'type': 'zoned', 'scale': 0}, # PIC 9(8)
    
    {'name': 'FL_OIL_PRORATION_EFF_DATE', 'start': 10, 'length': 8, 'type': 'zoned', 'scale': 0}, # CCYYMMDD
    {'name': 'FL_OIL_PRORATION_EFF_CENTURY', 'start': 10, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_PRORATION_EFF_YEAR', 'start': 12, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_PRORATION_EFF_MONTH', 'start': 14, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_PRORATION_EFF_DAY', 'start': 16, 'length': 2, 'type': 'zoned', 'scale': 0},
    
    {'name': 'FL_OIL_RULE_SUSPEND_DATE', 'start': 18, 'length': 8, 'type': 'zoned', 'scale': 0}, # CCYYMMDD
    {'name': 'FL_OIL_RULE_SUSPEND_CENTURY', 'start': 18, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_RULE_SUSPEND_YEAR', 'start': 20, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_RULE_SUSPEND_MONTH', 'start': 22, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_RULE_SUSPEND_DAY', 'start': 24, 'length': 2, 'type': 'zoned', 'scale': 0},
    
    # Filler 8 bytes at 26 (Pos 27)
    {'name': 'FL_OIL_DOCKET_SUFFIX', 'start': 34, 'length': 3, 'type': 'string'},
    {'name': 'FL_OIL_SPACING_TO_LEASE_LINE', 'start': 37, 'length': 4, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_SPACING_TO_WELL', 'start': 41, 'length': 4, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_ACRES_PER_UNIT', 'start': 45, 'length': 6, 'type': 'zoned', 'scale': 2}, # PIC 9(04)V99
    
    {'name': 'FL_OIL_TOLERANCE_ACRES_CODE', 'start': 51, 'length': 1, 'type': 'string'},
    {'name': 'FL_OIL_TOLERANCE_ACRES', 'start': 52, 'length': 5, 'type': 'zoned', 'scale': 2}, # PIC 9(03)V99
    
    {'name': 'FL_OIL_CASING_CODE', 'start': 57, 'length': 1, 'type': 'string'},
    {'name': 'FL_OIL_CASING_DEPTH', 'start': 58, 'length': 5, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_CASING_REMARKS', 'start': 63, 'length': 32, 'type': 'string'},
    
    {'name': 'FL_OIL_DIAGONAL_CODE', 'start': 95, 'length': 2, 'type': 'string'},
    {'name': 'FL_OIL_DIAGONAL', 'start': 97, 'length': 5, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_DIAGONAL_REMARKS', 'start': 102, 'length': 21, 'type': 'string'},
    
    {'name': 'FL_OIL_ALLOCATION_CODE', 'start': 123, 'length': 1, 'type': 'string'},
    {'name': 'FL_OIL_FIELD_TEXT', 'start': 124, 'length': 60, 'type': 'string'},
    
    {'name': 'FL_OIL_DOCKET_NUMBER', 'start': 184, 'length': 10, 'type': 'string'},
    # Redefines of Docket Number omitted for now, kept as string
    
    {'name': 'FL_OIL_RULES_NOT_RELIABLE_FLAG', 'start': 194, 'length': 1, 'type': 'string'},
]

OILAFORM_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_OIL_ALLOW_PERCENT_FACTOR', 'start': 2, 'length': 3, 'type': 'zoned', 'scale': 2}, # PIC 9V99
    {'name': 'FL_OIL_ALLOCATION_FCTR_CODE', 'start': 5, 'length': 2, 'type': 'string', 'lookup': OIL_ALLOCATION_FACTOR_LOOKUP},
]

OILRMRKS_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_OIL_REMARK_NUMBER', 'start': 2, 'length': 3, 'type': 'zoned', 'scale': 0}, # PIC 9(03)
    {'name': 'FL_OIL_REMARK_LINE_NO', 'start': 5, 'length': 3, 'type': 'zoned', 'scale': 0}, # PIC 9(03)
    
    {'name': 'FL_OIL_PRINT_ANNUAL_FLAG', 'start': 8, 'length': 1, 'type': 'string'},
    {'name': 'FL_OIL_PRINT_LEDGER_FLAG', 'start': 9, 'length': 1, 'type': 'string'},
    {'name': 'FL_OIL_PRINT_SCHEDULE_FLAG', 'start': 10, 'length': 1, 'type': 'string'},
    {'name': 'FL_OIL_PRINT_ON_LINE_FLAG', 'start': 11, 'length': 1, 'type': 'string'},
    
    {'name': 'FL_OIL_REMARK_DATE', 'start': 12, 'length': 8, 'type': 'zoned', 'scale': 0}, # CCYYMMDD
    {'name': 'FL_OIL_REMARK_DATE_CC', 'start': 12, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_REMARK_DATE_YY', 'start': 14, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_REMARK_DATE_MM', 'start': 16, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_OIL_REMARK_DATE_DD', 'start': 18, 'length': 2, 'type': 'zoned', 'scale': 0},
    
    {'name': 'FL_OIL_REMARK_TEXT', 'start': 20, 'length': 66, 'type': 'string'},
]

OILFTROT_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_OIL_FACTOR_CYCLE_KEY', 'start': 2, 'length': 4, 'type': 'zoned', 'scale': 0}, # PIC 9(04)
    {'name': 'FL_OIL_PROD_FACT_EXEMPT_FLAG', 'start': 6, 'length': 1, 'type': 'string'},
    {'name': 'FL_OIL_PROD_FACTOR', 'start': 7, 'length': 8, 'type': 'packed', 'scale': 7},         # PIC S9(8)V9(7) COMP-3 (8 bytes)
    {'name': 'FL_OIL_SPLIT_PROD_FACTOR', 'start': 15, 'length': 8, 'type': 'packed', 'scale': 7},   # PIC S9(8)V9(7) COMP-3 (8 bytes)
    {'name': 'FL_OIL_SPLIT_PROD_FACTOR_DATE', 'start': 23, 'length': 2, 'type': 'zoned', 'scale': 0}, # PIC 9(2)
    {'name': 'FL_OIL_UNWORKABLE_RES_MER', 'start': 25, 'length': 1, 'type': 'string'},
]

OILAFACT_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_OIL_FACTOR_CODE', 'start': 2, 'length': 2, 'type': 'string', 'lookup': ALLOCATION_FACTOR_LOOKUP},
    {'name': 'FL_OIL_ALLOCATION_FACTOR', 'start': 4, 'length': 8, 'type': 'packed', 'scale': 7}, # PIC S9(8)V9(7) COMP-3 (8 bytes)
]

OLCOUNTY_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_OIL_COUNTY_CODE', 'start': 2, 'length': 3, 'type': 'zoned', 'scale': 0}, # PIC 9(03)
]

OLOPTRUL_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_OIL_OPT_KEY', 'start': 2, 'length': 2, 'type': 'zoned', 'scale': 0}, # PIC 9(02)
    {'name': 'FL_OIL_OPT_SPACE_TO_LEASE_LINE', 'start': 4, 'length': 4, 'type': 'zoned', 'scale': 0}, # PIC 9(04)
    {'name': 'FL_OIL_OPT_SPACE_TO_WELL', 'start': 8, 'length': 4, 'type': 'zoned', 'scale': 0}, # PIC 9(04)
    {'name': 'FL_OIL_OPT_ACRES_PER_UNIT', 'start': 12, 'length': 6, 'type': 'zoned', 'scale': 2}, # PIC 9(04)V99
    {'name': 'FL_OIL_OPT_TOLERANCE_ACRES', 'start': 18, 'length': 5, 'type': 'zoned', 'scale': 2}, # PIC 9(03)V99
    {'name': 'FL_OIL_OPT_DIAGONAL_CODE', 'start': 23, 'length': 2, 'type': 'string'},
    {'name': 'FL_OIL_OPT_DIAGONAL_FEET', 'start': 25, 'length': 5, 'type': 'zoned', 'scale': 0}, # PIC 9(05)
    {'name': 'FL_OIL_OPT_FIELD_TEXT', 'start': 30, 'length': 47, 'type': 'string'},
]
