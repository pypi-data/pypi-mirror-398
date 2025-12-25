
ASHEET_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_AS_BALANCING_PERIOD_CENT', 'start': 2, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_BALANCING_PERIOD_YEAR', 'start': 4, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_BALANCING_PERIOD_MONTH', 'start': 6, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_USER_UPDT_CUR_6MO_FLAG', 'start': 8, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_USER_UPDT_PRIOR_6MO_FLAG', 'start': 9, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_CURRENT_6MO_STATUS', 'start': 10, 'length': 5, 'type': 'packed', 'scale': 0}, # S9(9) COMP-3
    {'name': 'FL_AS_PRIOR_6MO_STATUS', 'start': 15, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_TOT_PRIOR_XTRA_ADJ_AMT', 'start': 20, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_WORKING_PRIOR_AMOUNT', 'start': 25, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_ACTIVE_INACTIVE_FLAG', 'start': 30, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_CALC_IN_EFF_CENTURY', 'start': 31, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_CALC_IN_EFF_YEAR', 'start': 33, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_CALC_IN_EFF_MON', 'start': 35, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_PRIOR_REINSTATED', 'start': 37, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_CURRENT_REINSTATED', 'start': 42, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_PAGE_NUMBER', 'start': 47, 'length': 4, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_UPDATE_FLAG', 'start': 51, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_EXTRACT_CENTURY', 'start': 52, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_EXTRACT_YEAR', 'start': 54, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_EXTRACT_MONTH', 'start': 56, 'length': 2, 'type': 'zoned', 'scale': 0},
]



ASHEETMO_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_AS_SCHED_CENTURY', 'start': 2, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_SCHED_YEAR', 'start': 4, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_SCHED_MONTH', 'start': 6, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_RECAL_ALLOC_FCT_CNT', 'start': 8, 'length': 1, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_NUMBER_OF_ASHEETS', 'start': 9, 'length': 1, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_CURRENT_FORECAST', 'start': 10, 'length': 5, 'type': 'packed', 'scale': 0}, # S9(9)
    {'name': 'FL_AS_3RD_MO_PRIOR_FORECAST', 'start': 15, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_3RD_MO_PRIOR_SUP_CHNG', 'start': 20, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_NON_LIMITED_PROD', 'start': 25, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_GROSS_ADJUSTMENT_AMT', 'start': 30, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_LIMITED_ALLOWABLE', 'start': 35, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_LIMITED_PRODUCTION', 'start': 40, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_LIMITED_ADJUSTMENT', 'start': 45, 'length': 5, 'type': 'packed', 'scale': 0}, # S9(8) still 5 bytes
    {'name': 'FL_AS_NORMAL_ADJUSTMENT', 'start': 50, 'length': 5, 'type': 'packed', 'scale': 0}, # S9(8)
    {'name': 'FL_AS_EXTRA_ADJUSTMENT', 'start': 55, 'length': 4, 'type': 'packed', 'scale': 0}, # S9(7) is 4 bytes
    {'name': 'FL_AS_TOTAL_ASSIGNED_RES_AMT', 'start': 59, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_CANCEL_UNDERAGE_AMT', 'start': 64, 'length': 4, 'type': 'packed', 'scale': 0}, # S9(7)
    # Missing fields added:
    {'name': 'FL_AS_CURRENT_FORECAST_CODE', 'start': 68, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_COL_1_REVISED_CODE', 'start': 69, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_3RD_MO_PRIOR_FRCST_CODE', 'start': 70, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_COL_2_REVISED_CODE', 'start': 71, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_COL_3_REVISED_CODE', 'start': 72, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_COL_4_REVISED_CODE', 'start': 73, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_COL_5_REVISED_CODE', 'start': 74, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_COL_6_REVISED_CODE', 'start': 75, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_COL_7_REVISED_CODE', 'start': 76, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_COL_8_REVISED_CODE', 'start': 77, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_COL_10_REVISED_CODE', 'start': 78, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_TOT_ASSIGN_RES_AMT_CD', 'start': 79, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_NUM_OF_MONS_AVGD', 'start': 80, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_COL_11_REVISED_CODE', 'start': 82, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_USER_UPD_CALC_EFF_FLAG', 'start': 83, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_CANCEL_UNDERAGE_CODE', 'start': 84, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_ITEM_12_REVISED_CODE', 'start': 85, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_SPECIAL_ALLOWABLE_FLAG', 'start': 86, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_REDUCED_RATE_FLAG', 'start': 87, 'length': 1, 'type': 'string'},
    {'name': 'FL_AS_FIELD_BALANCED_FLAG', 'start': 88, 'length': 1, 'type': 'string'},

    {'name': 'FL_AS_TOT_CALC_RES_AMOUNT', 'start': 89, 'length': 5, 'type': 'packed', 'scale': 0}, # Pos 90
    
    {'name': 'FL_AS_INTEND_TO_RECALC_FLAG', 'start': 94, 'length': 1, 'type': 'string'}, # Pos 95

    {'name': 'FL_AS_GROSS_T3_TOTAL', 'start': 95, 'length': 5, 'type': 'packed', 'scale': 0}, # Pos 96
    {'name': 'FL_AS_ADJUSTED_T3_TOTAL', 'start': 100, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_GROSS_DELIV', 'start': 105, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_ADJUSTED_DELIV', 'start': 110, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_COR_3RD_MO_PRI_SUP_CHG', 'start': 115, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_TOT_CURR_XTRA_ADJ_AMT', 'start': 120, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_WORKING_CUR_XTRA_ADJ_AMT', 'start': 125, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_MONTHLY_CUMU_STATUS', 'start': 130, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_PROJECTED_STATUS', 'start': 135, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_AS_MAX_DELIV', 'start': 140, 'length': 5, 'type': 'packed', 'scale': 0},
    
    {'name': 'FL_AS_USER_UPD_MAX_DEL_FLAG', 'start': 145, 'length': 1, 'type': 'string'}, # Pos 146

    {'name': 'FL_AS_P_CUR_ALOW_CUR_FRCST', 'start': 146, 'length': 3, 'type': 'zoned', 'scale': 0}, # Pos 147
    {'name': 'FL_AS_P_CUR_ALOW_6_MO_AVG_PRD', 'start': 149, 'length': 3, 'type': 'zoned', 'scale': 0}, # Pos 150
    {'name': 'FL_AS_P_6_MO_AVG_PRD_6_MO_AVG', 'start': 152, 'length': 3, 'type': 'zoned', 'scale': 0}, # Pos 153

    {'name': 'FL_AS_CALC_ASHEET_CENTURY', 'start': 155, 'length': 2, 'type': 'zoned', 'scale': 0}, # Pos 156
    {'name': 'FL_AS_CALC_ASHEET_YEAR', 'start': 157, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_CALC_ASHEET_MONTH', 'start': 159, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AS_CALC_ASHEET_DAY', 'start': 161, 'length': 2, 'type': 'zoned', 'scale': 0},
]

FLT3ROOT_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_T3_NOMINATOR_NUMBER', 'start': 2, 'length': 6, 'type': 'zoned', 'scale': 0}, # PIC 9(06)
    {'name': 'FL_T3_SYSTEM_NUMBER', 'start': 8, 'length': 4, 'type': 'zoned', 'scale': 0},    # PIC 9(04)
]

FLDT3_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_T3_REPORT_DATE', 'start': 2, 'length': 6, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_T3_REPORT_CENTURY', 'start': 2, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_T3_REPORT_YEAR', 'start': 4, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_T3_REPORT_MONTH', 'start': 6, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_T3_KIND_OF_GAS', 'start': 8, 'length': 1, 'type': 'string'},
    {'name': 'FL_T3_PERC_FLD_DEL', 'start': 9, 'length': 3, 'type': 'zoned', 'scale': 2}, # 9V99 = 3 digits, scaled
    {'name': 'FL_T3_POSTING_CENTURY', 'start': 12, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_T3_POSTING_YEAR', 'start': 14, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_T3_POSTING_MONTH', 'start': 16, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_T3_POSTING_DAY', 'start': 18, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_T3_CORRECTED_REPORT', 'start': 20, 'length': 1, 'type': 'string'},
    {'name': 'FL_T3_AMOUNT_OF_GAS', 'start': 21, 'length': 9, 'type': 'zoned', 'scale': 0}, # PIC 9(09) -> Zoned 9 bytes
    {'name': 'FL_T3_BATCH_NUMBER', 'start': 30, 'length': 3, 'type': 'zoned', 'scale': 0},
]

FLDMO_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_PRODUCTION_DATE', 'start': 2, 'length': 6, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_PRODUCTION_CENTURY', 'start': 2, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_PRODUCTION_YEAR', 'start': 4, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_PRODUCTION_MONTH', 'start': 6, 'length': 2, 'type': 'zoned', 'scale': 0},
    # Filler 2 bytes at 8
    {'name': 'FL_GAS_ALLOWABLE', 'start': 10, 'length': 7, 'type': 'packed', 'scale': 0}, # PIC 9(13) COMP-3 (7 bytes)
    {'name': 'FL_LIQUID_COND_ALLOWABLE', 'start': 17, 'length': 5, 'type': 'packed', 'scale': 0}, # PIC 9(09) COMP-3 (5 bytes)
    {'name': 'FL_OIL_ALLOWABLE', 'start': 22, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_CASINGHEAD_GAS_LIMIT', 'start': 27, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_P2_GAS_PRODUCTION', 'start': 32, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_P2_CONDENSATE_PRODUCTION', 'start': 37, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_PARTIAL_GAS_WELL_PROD_CD', 'start': 42, 'length': 1, 'type': 'string'},
    {'name': 'FL_P1_OIL_PRODUCTION', 'start': 43, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_P1_CASINGHEAD_PRODUCTION', 'start': 48, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_PARTIAL_OIL_WELL_PROD_CD', 'start': 53, 'length': 1, 'type': 'string'},
    {'name': 'FL_CENT_LAST_UPDATED', 'start': 54, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_YEAR_LAST_UPDATED', 'start': 56, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_MONTH_LAST_UPDATED', 'start': 58, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_DAY_LAST_UPDATED', 'start': 60, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_UNLIMITED_CASINGHEAD_FLAG', 'start': 62, 'length': 1, 'type': 'string'},
    {'name': 'FL_INCLUDE_DROP_GAS_STATS_FLAG', 'start': 63, 'length': 1, 'type': 'string'},
    {'name': 'FL_INCLUDE_DROP_OIL_STATS_FLAG', 'start': 64, 'length': 1, 'type': 'string'},
    {'name': 'FL_TOTAL_CALC_RES_AMOUNT', 'start': 65, 'length': 5, 'type': 'packed', 'scale': 0},
]

CALC49B_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_GAS_ALLOW_EFFECTIVE_DATE', 'start': 2, 'length': 8, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_ALLOW_EFFECTIVE_CC', 'start': 2, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_ALLOW_EFFECTIVE_YY', 'start': 4, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_ALLOW_EFFECTIVE_MM', 'start': 6, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_GAS_ALLOW_EFFECTIVE_DD', 'start': 8, 'length': 2, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_RRCID_DETERMINING_WELL', 'start': 10, 'length': 6, 'type': 'zoned', 'scale': 0},
    # Filler 2 bytes at 16
    {'name': 'FL_G_1_GAS_GRAVITY', 'start': 18, 'length': 3, 'type': 'zoned', 'scale': 3}, # PIC V999
    {'name': 'FL_AVG_RESERVOIR_BHP', 'start': 21, 'length': 5, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_AVG_RESERVOIR_BH_TEMP', 'start': 26, 'length': 3, 'type': 'zoned', 'scale': 0},
    {'name': 'FL_FORMATION_VOLUME_FACTOR', 'start': 29, 'length': 5, 'type': 'zoned', 'scale': 4}, # PIC 9V9(04)
    {'name': 'FL_SOLUTION_GAS_OIL_RATIO', 'start': 34, 'length': 9, 'type': 'zoned', 'scale': 4}, # PIC 9(05)V9(04)
    {'name': 'FL_DEVIATION_FACTOR', 'start': 43, 'length': 5, 'type': 'zoned', 'scale': 4}, # PIC 9V9(04)
    {'name': 'FL_TOP_DAILY_GAS_ALLOW_CU_FT', 'start': 48, 'length': 6, 'type': 'packed', 'scale': 0}, # PIC 9(11) COMP-3 (6 bytes)
    {'name': 'FL_TOP_DAILY_GAS_ALLOW_MCF', 'start': 54, 'length': 4, 'type': 'packed', 'scale': 0}, # PIC 9(07) COMP-3 (4 bytes)
]
