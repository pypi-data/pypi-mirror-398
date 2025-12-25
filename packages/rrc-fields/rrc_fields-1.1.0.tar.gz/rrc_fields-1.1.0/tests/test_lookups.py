import sys
import os

# Ensure src is in python path
# When running from tests/, we need to go up one level to find src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from rrc_fields.layouts import lookups
    print("Successfully imported lookups module")
except ImportError as e:
    print(f"Failed to import lookups: {e}")
    sys.exit(1)

def verify_lookup(name, lookup_dict, expected_pairs):
    print(f"Verifying {name}...")
    errors = []
    for key, val in expected_pairs.items():
        if key not in lookup_dict:
            errors.append(f"Missing key: {key}")
        elif lookup_dict[key] != val:
            errors.append(f"Incorrect value for {key}: expected '{val}', got '{lookup_dict[key]}'")
    
    if errors:
        for err in errors:
            print(f"  X {err}")
        return False
    print("  OK")
    return True

all_checks_passed = True

# FL-FIELD-CLASS
if not verify_lookup("FIELD_CLASS_LOOKUP", lookups.FIELD_CLASS_LOOKUP, {
    'G': 'GAS FIELD',
    'O': 'OIL FIELD',
    'B': 'OIL AND GAS FIELD'
}):
    all_checks_passed = False

# FL-FORMATION-COMPOSITION
if not verify_lookup("FORMATION_COMPOSITION_LOOKUP", lookups.FORMATION_COMPOSITION_LOOKUP, {
    'SS': 'SANDSTONE',
    'DL': 'DOLOMITE-LIME'
}):
    all_checks_passed = False

# FL-4-MONTH-TEST-EXCPT
if not verify_lookup("FOUR_MONTH_TEST_EXCPT_LOOKUP", lookups.FOUR_MONTH_TEST_EXCPT_LOOKUP, {
    '1': 'ONE-MONTH TEST',
    '4': 'FOUR-MONTH TEST'
}):
    all_checks_passed = False

# FL-HYDROGEN-SULFIDE-CD
if not verify_lookup("HYDROGEN_SULFIDE_CODE_LOOKUP", lookups.HYDROGEN_SULFIDE_CODE_LOOKUP, {
    'N': 'NO HYDROGEN SULFIDE PRESENT',
    'E': 'HYDROGEN SULFIDE PRESENT BUT EXEMPT FROM FILING'
}):
    all_checks_passed = False

# FL-GAS-OIL-RATIO-CODE
if not verify_lookup("GAS_OIL_RATIO_CODE_LOOKUP", lookups.GAS_OIL_RATIO_CODE_LOOKUP, {
    'G': 'GAS OIL RATIO',
    'K': 'GAS LIMIT BASED ON TOP WELL\'S LIMIT'
}):
    all_checks_passed = False

# FL-NET-GOR-RULE-CODE
if not verify_lookup("NET_GOR_RULE_CODE_LOOKUP", lookups.NET_GOR_RULE_CODE_LOOKUP, {
    'R': 'REGULAR FIELD',
    'U': 'NET UNLIMITED AMOUNT'
}):
    all_checks_passed = False

# FL-TYPE-FIELD-CODE
if not verify_lookup("GAS_FIELD_TYPE_LOOKUP", lookups.GAS_FIELD_TYPE_LOOKUP, {
    'A': 'ASSOCIATED FIELD',
    'N': 'NON-ASSOCIATED FIELD'
}):
    all_checks_passed = False

# FL-GAS-TEST-FREQUENCY
if not verify_lookup("GAS_TEST_FREQUENCY_LOOKUP", lookups.GAS_TEST_FREQUENCY_LOOKUP, {
    'A': 'ANNUAL TESTING (ONCE PER YEAR)',
    'S': 'SEMI-ANNUAL TESTING (TWICE PER YEAR)'
}):
    all_checks_passed = False

# FL-PRI-TEST-MON-G10-REQUIRE
if not verify_lookup("G10_REQUIREMENT_LOOKUP", lookups.G10_REQUIREMENT_LOOKUP, {
    'B': 'DELIVERABILITY, FLOWING PRESSURE, SIWH PRESSURE',
    'K': 'COMMINGLING TEST IN FIELD TESTING ANNUALLY - LIQUID GRAVITY AND GOR'
}):
    all_checks_passed = False

# FL-GAS-EXEMPT-MINIMUM-GOR
if not verify_lookup("GAS_EXEMPT_MIN_GOR_LOOKUP", lookups.GAS_EXEMPT_MIN_GOR_LOOKUP, {
    'N': 'NOT EXEMPT - MINIMUM GOR',
    'Y': 'EXEMPT - MINIMUM GOR'
}):
    all_checks_passed = False

# FL-OFFSHORE-CODE
if not verify_lookup("OFFSHORE_CODE_LOOKUP", lookups.OFFSHORE_CODE_LOOKUP, {
    'L ': 'LAND',
    'SF': 'STATE-FEDERAL'
}):
    all_checks_passed = False

# FL-SALT-DOME-EXEMPTION
if not verify_lookup("SALT_DOME_EXEMPTION_LOOKUP", lookups.SALT_DOME_EXEMPTION_LOOKUP, {
    'Y': 'EXEMPT - SWR SALT DOME'
}):
    all_checks_passed = False

# FL-COUNTY-REGULAR-EXEMPTION
if not verify_lookup("COUNTY_REGULAR_EXEMPTION_LOOKUP", lookups.COUNTY_REGULAR_EXEMPTION_LOOKUP, {
    'Y': 'EXEMPT - SWR CNTY REGULAR'
}):
    all_checks_passed = False

# FL-GAS-CONSOLIDATED-FIELD-FLAG
if not verify_lookup("GAS_CONSOLIDATED_FIELD_FLAG_LOOKUP", lookups.GAS_CONSOLIDATED_FIELD_FLAG_LOOKUP, {
    'Y': 'GAS CONSOLIDATED FIELD'
}):
    all_checks_passed = False

# FL-GAS-TYPE-FIELD-CODE
if not verify_lookup("GAS_TYPE_FIELD_CODE_LOOKUP", lookups.GAS_TYPE_FIELD_CODE_LOOKUP, {
    '49': 'FL-49B',
    'SP': 'FL-SPECIAL'
}):
    all_checks_passed = False

# FL-GAS-LIMITED-PROD-ALLOWABLE
if not verify_lookup("GAS_LIMITED_PROD_ALLOWABLE_LOOKUP", lookups.GAS_LIMITED_PROD_ALLOWABLE_LOOKUP, {
    '6M': 'FL-REGULAR-6-MON-MONTHLY',
    '3D': 'FL-SPECIAL-3-MON-HIGH-DAILY',
    'NO': 'FL-NO-LIMITED-PROD-ALLOWABLE'
}):
    all_checks_passed = False

# FL-GAS-BALANCE-RULE-CODE
if not verify_lookup("GAS_BALANCE_RULE_CODE_LOOKUP", lookups.GAS_BALANCE_RULE_CODE_LOOKUP, {
    'N': 'FL-NO-BALANCING',
    'L': 'FL-BALANCE-LIMITED-WITH-UNDER'
}):
    all_checks_passed = False

# FL-GAS-NO-PAST-PRODUCTION-FLAG
if not verify_lookup("GAS_NO_PAST_PROD_FLAG_LOOKUP", lookups.GAS_NO_PAST_PROD_FLAG_LOOKUP, {
    'N': 'FL-GAS-DONT-USE-PAST-PROD'
}):
    all_checks_passed = False

# FL-GAS-NO-HIGHEST-DAILY-FLAG
if not verify_lookup("GAS_NO_HIGHEST_DAILY_FLAG_LOOKUP", lookups.GAS_NO_HIGHEST_DAILY_FLAG_LOOKUP, {
    'N': 'FL-GAS-DONT-USE-HIGHEST-DLY'
}):
    all_checks_passed = False

# FL-GAS-LIMIT-ALLOW-HEARING-FLG
if not verify_lookup("GAS_LIMIT_ALLOW_HEARING_FLAG_LOOKUP", lookups.GAS_LIMIT_ALLOW_HEARING_FLAG_LOOKUP, {
    'Y': 'FL-GAS-LIMIT-ALLOW-BY-HEARING'
}):
    all_checks_passed = False

# FL-GAS-CAPABILITY-REVIEW-FLAG
if not verify_lookup("GAS_CAPABILITY_REVIEW_FLAG_LOOKUP", lookups.GAS_CAPABILITY_REVIEW_FLAG_LOOKUP, {
    'Y': 'FL-GAS-ONE-MONTH-REVIEW'
}):
    all_checks_passed = False

# FL-ELIGIBLE-FOR-250-SPEC-FLAG
if not verify_lookup("ELIGIBLE_FOR_250_SPEC_FLAG_LOOKUP", lookups.ELIGIBLE_FOR_250_SPEC_FLAG_LOOKUP, {
    'Y': 'FL-HAS-250-K1-ALLOW',
    'N': 'FL-GAS-SPECL-FLD-RULES-EXIST'
}):
    all_checks_passed = False

# FL-SIWH-EXCEPTION-FLAG
if not verify_lookup("SIWH_EXCEPTION_FLAG_LOOKUP", lookups.SIWH_EXCEPTION_FLAG_LOOKUP, {
    'Y': 'FL-SIWH-EXCEPTION'
}):
    all_checks_passed = False


if all_checks_passed:
    print("\nAll verifications passed!")
    sys.exit(0)
else:
    print("\nSome verifications failed.")
    sys.exit(1)
