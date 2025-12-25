
FLMKTDMD_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_MKT_DEMAND_SCHED_CCYY', 'start': 2, 'length': 4, 'type': 'zoned'},
    {'name': 'FL_MKT_DEMAND_SCHED_MM', 'start': 6, 'length': 2, 'type': 'zoned'},
    {'name': 'FL_MKT_DEMAND_FORECAST', 'start': 8, 'length': 5, 'type': 'packed', 'scale': 0}, # 9 digits = 5 bytes
    {'name': 'FL_MKT_DEMAND_CAPABILITY', 'start': 13, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_MKT_DMD_FORECAST_CORR_ADJ', 'start': 18, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_MKT_DEMAND_SUPP_CHG_ADJ', 'start': 23, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_MKT_DEMAND_COMMISSION_ADJ', 'start': 28, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_MKT_DEMAND_REV_FORECAST', 'start': 33, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_MKT_DMD_ADJ_RES_FORECAST', 'start': 38, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_MKT_DMD_CALC_RES_FORECAST', 'start': 43, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_MKT_DMD_TOTAL_RES_FORECAST', 'start': 48, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_MKT_DMD_HEARING_SPEC_AMT', 'start': 53, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_MKT_DMD_3RD_MONTH_PREVIOUS', 'start': 58, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_MKT_DMD_SPECIAL_UNDERAGE', 'start': 63, 'length': 9, 'type': 'zoned', 'scale': 0}, # Zoned Decimal S9(09)
    {'name': 'FL_MKT_DMD_PRECALC_ALLOWABLE', 'start': 72, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_MKT_DMD_PRECALC_ALLOWABLE', 'start': 72, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_MKT_DMD_12_MONTH_PEAK', 'start': 77, 'length': 5, 'type': 'packed', 'scale': 0},
]

OPRMKTDM_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_OPERATOR_NUMBER', 'start': 2, 'length': 6, 'type': 'string'}, # PIC 9(06)
    {'name': 'FL_OPR_MKT_DMD_FORECAST', 'start': 8, 'length': 5, 'type': 'packed', 'scale': 0}, # S9(09) COMP-3
    {'name': 'FL_OPR_MKT_DMD_OPT_FORECAST', 'start': 13, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OPR_CAPABILITY', 'start': 18, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OPR_SUBSTITUTE_CAPABILITY', 'start': 23, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OPR_MKT_DMD_ADJ_FORECAST', 'start': 28, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OPR_MKT_DMD_REV_FORECAST', 'start': 33, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OPR_MKT_DMD_G10_TOTAL', 'start': 38, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OPR_MKT_DMD_HIGH_PROD_TOTAL', 'start': 43, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OPR_MKT_DMD_HIGH_PROD_WELLS', 'start': 48, 'length': 3, 'type': 'packed', 'scale': 0}, # S9(05) COMP-3
    {'name': 'FL_OPR_MKT_DMD_SUB_CAP_WELLS', 'start': 51, 'length': 3, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OPR_MKT_DMD_G10_WELLS', 'start': 54, 'length': 3, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OPR_MKT_DMD_DELQ_P2_WELLS', 'start': 57, 'length': 3, 'type': 'packed', 'scale': 0},
    {'name': 'FL_OPR_MKT_DMD_3RD_MO_PREV', 'start': 60, 'length': 5, 'type': 'packed', 'scale': 0},
    {'name': 'FL_MD_1_RECEIVED_FLAG', 'start': 65, 'length': 1, 'type': 'string'},
    {'name': 'FL_OPR_MKT_DMD_12_MONTH_PEAK', 'start': 66, 'length': 5, 'type': 'packed', 'scale': 0},
]

FLMKTRMK_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_MKT_DMD_COMM_ADJ_REMARKS', 'start': 2, 'length': 80, 'type': 'string'},
]

FLSUPRMK_LAYOUT = [
    {'name': 'RRC_TAPE_RECORD_ID', 'start': 0, 'length': 2, 'type': 'string'},
    {'name': 'FL_MKT_DMD_SUPP_ADJ_REMARKS', 'start': 2, 'length': 80, 'type': 'string'},
]
