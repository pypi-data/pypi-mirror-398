import unittest
import codecs
from rrc_fields import RRCFieldParser
from rrc_fields.layouts import FLDROOT_LAYOUT

class TestRRCLayouts(unittest.TestCase):
    def setUp(self):
        self.parser = RRCFieldParser(encoding='cp037')

    def test_fldroot_parsing(self):
        # Create a 240-byte record (size of FLDROOT segment + filler is 240 in reality based on typical tape block sizes or minimal size)
        # But for parse_record, we just need enough bytes for the layout.
        # The specific layout goes up to byte 142 (end of FL_MANUAL_REVIEW_FLAG).
        # We'll stick to the layout end.
        
        # We construct a record by filling it with 0x00 (or spaces 0x40) and then patching specifics.
        # But easier to build it field by field or just patch a bytearray.
        
        # Initialize with EBCDIC spaces (0x40)
        record = bytearray([0x40] * 200) 
        
        # Helper to set bytes
        def set_bytes(start, hex_str):
             b = bytes.fromhex(hex_str)
             record[start:start+len(b)] = b
             
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b

        def set_zoned(start, number, length, signed=False):
            # Simple helper to create zoned decimal bytes
            s = str(abs(number)).zfill(length)
            encoded = []
            for i, digit in enumerate(s):
                val = 0xF0 + int(digit) # standard unsigned
                if i == len(s) - 1:
                     if number < 0:
                         val = 0xD0 + int(digit)
                     elif signed and number >= 0:
                         val = 0xC0 + int(digit)
                encoded.append(val)
            record[start:start+len(encoded)] = bytes(encoded)

        # 01 RAILROAD-COMMISSION-TAPE-REC
        # 02 RRC-TAPE-RECORD-ID PIC X(02). -> Pos 0. Value '01'
        set_ebcdic(0, '01')
        
        # 03 FL-ROOT-KEY
        # 05 FL-DISTRICT PIC X(2). -> Pos 2. Value '03'
        set_ebcdic(2, '03')
        
        # 05 FL-NUMBER PIC 9(8). -> Pos 4. Value 12345678
        set_zoned(4, 12345678, 8)
        
        # 03 FL-NAME PIC X(32). -> Pos 12. "TEST FIELD NAME"
        set_ebcdic(12, "TEST FIELD NAME")
        
        # 03 FL-FIELD-CLASS PIC X(01). -> Pos 44. 'O'
        set_ebcdic(44, "O")

        # 03 FL-OIL-DISC-WELL-GRAVITY PIC S9(2)V9(1). -> Pos 97 (Length 3). Value -12.3
        # -123 -> F1 F2 D3
        set_zoned(97, -123, 3, signed=True)
        
        # Parse
        parsed = self.parser.parse_record(bytes(record), FLDROOT_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '01')
        self.assertEqual(parsed['FL_DISTRICT'], '03')
        self.assertEqual(parsed['FL_NUMBER'], 12345678)
        self.assertEqual(parsed['FL_NAME'], 'TEST FIELD NAME')
        self.assertEqual(parsed['FL_FIELD_CLASS'], 'O')
        self.assertEqual(parsed['FL_OIL_DISC_WELL_GRAVITY'], -12.3)

    def test_gasseg_parsing(self):
        # Create a mock GASSEG record
        # Layout uses packed fields heavily.
        
        from rrc_fields.layouts import GASSEG_LAYOUT
        
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_packed(start, number, length, scale=0):
            # Simple packed encoder helper
            # Convert number to string digits
            s = str(abs(int(number * (10**scale))))
            if len(s) % 2 == 0:
                s = '0' + s # Pad for sign nibble to be at end of byte
            
            # e.g. 123 -> '0123' -> 01 23 :: But need sign nibble
            # Packed format: Digits then Sign. 1 digit per nibble.
            # 123 -> 12 3F (Positive)
            # length is bytes. 2 digits per byte minus 1 nibble for sign.
            # Capacity = 2*length - 1 digits.
            
            digits = []
            for char in s:
                digits.append(int(char))
                
            # Pad with leading zeros to fill the requested byte length
            # Target nibbles = length * 2
            # Use last nibble for sign
            
            target_nibbles = length * 2
            current_nibbles = len(digits) + 1 # +1 for sign
            
            padding = target_nibbles - current_nibbles
            nibbles = [0] * padding + digits
            
            # Sign nibble
            sign = 0xC if number >= 0 else 0xD
            nibbles.append(sign)
            
            # Pack into bytes
            packed_bytes = bytearray()
            for i in range(0, len(nibbles), 2):
                byte = (nibbles[i] << 4) | nibbles[i+1]
                packed_bytes.append(byte)
                
            record[start:start+len(packed_bytes)] = packed_bytes


        # 02 RRC-TAPE-RECORD-ID PIC X(02). -> Pos 0 '02'
        set_ebcdic(0, '02')
        # 03 FL-GASSEG-KEY PIC X(01) VALUE 'G'. -> Pos 2
        set_ebcdic(2, 'G')
        
        # Test a packed field:
        # FL_CUM_GAS_PRODUCTION_TO_CONV at 49, len 7, scale 0.
        # Let's put 12345 in it.
        set_packed(49, 12345, 7)
        
        parsed = self.parser.parse_record(bytes(record), GASSEG_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '02')
        self.assertEqual(parsed['FL_GASSEG_KEY'], 'G')
        self.assertEqual(parsed['FL_CUM_GAS_PRODUCTION_TO_CONV'], 12345)

    def test_flmktdmd_parsing(self):
        # 03 FLMKTDMD
        from rrc_fields.layouts import FLMKTDMD_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, signed=False):
            # Simple helper to create zoned decimal bytes
            s = str(abs(number)).zfill(length)
            encoded = []
            for i, digit in enumerate(s):
                val = 0xF0 + int(digit) # standard unsigned
                if i == len(s) - 1:
                     if number < 0:
                         val = 0xD0 + int(digit)
                     elif signed and number >= 0:
                         val = 0xC0 + int(digit)
                encoded.append(val)
            record[start:start+len(encoded)] = bytes(encoded)
            
        # 02 RRC-TAPE-RECORD-ID -> 03
        set_ebcdic(0, '03')
        
        # FL-MKT-DMD-SPECIAL-UNDERAGE at 63, length 9. Zoned.
        set_zoned(63, 123456789, 9, signed=True)
        
        parsed = self.parser.parse_record(bytes(record), FLMKTDMD_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '03')
        self.assertEqual(parsed['FL_MKT_DMD_SPECIAL_UNDERAGE'], 123456789)

    def test_oprmktdm_parsing(self):
        # 04 OPRMKTDM
        from rrc_fields.layouts import OPRMKTDM_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_packed(start, number, length, scale=0):
             # Simplified duplicate of local set_packed for this test method
             # In real refactor, iterate over helpers?
            s = str(abs(int(number * (10**scale))))
            if len(s) % 2 == 0:
                s = '0' + s 
            
            digits = []
            for char in s:
                digits.append(int(char))
                
            target_nibbles = length * 2
            current_nibbles = len(digits) + 1 
            
            padding = target_nibbles - current_nibbles
            nibbles = [0] * padding + digits
            
            sign = 0xC if number >= 0 else 0xD
            nibbles.append(sign)
            
            packed_bytes = bytearray()
            for i in range(0, len(nibbles), 2):
                byte = (nibbles[i] << 4) | nibbles[i+1]
                packed_bytes.append(byte)
            record[start:start+len(packed_bytes)] = packed_bytes

        # 04 ID
        set_ebcdic(0, '04')
        set_ebcdic(65, 'Y') # FL_MD_1_RECEIVED_FLAG at 65
        set_packed(66, 999, 5) # FL_OPR_MKT_DMD_12_MONTH_PEAK at 66
        
        parsed = self.parser.parse_record(bytes(record), OPRMKTDM_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '04')
        self.assertEqual(parsed['FL_MD_1_RECEIVED_FLAG'], 'Y')
        self.assertEqual(parsed['FL_OPR_MKT_DMD_12_MONTH_PEAK'], 999)

    def test_flmktrmk_parsing(self):
        # 05 FLMKTRMK
        from rrc_fields.layouts import FLMKTRMK_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        set_ebcdic(0, '05')
        set_ebcdic(2, 'This is a test remark from the analyst.')
        
        parsed = self.parser.parse_record(bytes(record), FLMKTRMK_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '05')
        self.assertEqual(parsed['FL_MKT_DMD_COMM_ADJ_REMARKS'].strip(), 'This is a test remark from the analyst.')

    def test_flsuprmk_parsing(self):
        # 06 FLSUPRMK
        # Almost identical to 05
        from rrc_fields.layouts import FLSUPRMK_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        set_ebcdic(0, '06')
        set_ebcdic(2, 'Supplemental adjustment remark.')
        
        parsed = self.parser.parse_record(bytes(record), FLSUPRMK_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '06')
        self.assertEqual(parsed['FL_MKT_DMD_SUPP_ADJ_REMARKS'].strip(), 'Supplemental adjustment remark.')

    def test_gascycle_parsing(self):
        # 07 GASCYCLE
        from rrc_fields.layouts import GASCYCLE_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b

        def set_packed(start, number, length, scale=0):
             # Simplified duplicate 
            s = str(abs(int(number * (10**scale))))
            if len(s) % 2 == 0:
                s = '0' + s 
            
            digits = []
            for char in s:
                digits.append(int(char))
            
            target_nibbles = length * 2
            current_nibbles = len(digits) + 1 
            padding = target_nibbles - current_nibbles
            nibbles = [0] * padding + digits
            sign = 0xC if number >= 0 else 0xD
            nibbles.append(sign)
            
            packed_bytes = bytearray()
            for i in range(0, len(nibbles), 2):
                byte = (nibbles[i] << 4) | nibbles[i+1]
                packed_bytes.append(byte)
            record[start:start+len(packed_bytes)] = packed_bytes
            
        set_ebcdic(0, '07')
        set_ebcdic(2, '1997') # Key
        set_packed(15, 987654.32, 5, scale=2) # FL_GAS_EXCEPT_HIGH_DAY_AMOUNT (faked scale for test, layout has scale 0)
        # Re-check allowed scale in layout? Layout says scale 0.
        # Let's test with scale 0 integer.
        set_packed(15, 987654321, 5, scale=0)
        
        parsed = self.parser.parse_record(bytes(record), GASCYCLE_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '07')
        self.assertEqual(parsed['FL_GAS_CYCLE_KEY'], '1997')
        self.assertEqual(parsed['FL_GAS_EXCEPT_HIGH_DAY_AMOUNT'], 987654321)

    def test_gsfldrul_parsing(self):
        # 08 GSFLDRUL
        from rrc_fields.layouts import GSFLDRUL_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, signed=False):
            # Signed vs Unsigned Zoned
            # PIC 9(04) is unsigned. Last nibble is F usually, not C/D.
            # But standard checks usually handle C/D/F as sign nibbles.
            # python's simple unzone often just masks the zone nibble.
            # Let's create 'unsigned' style zoned: F1 F2 F3 F4
            s = str(abs(number)).zfill(length)
            encoded = []
            for i, digit in enumerate(s):
                # Standard unsigned EBCDIC digit is 0xF0 + digit
                val = 0xF0 + int(digit) 
                
                # If signed, replace last zone with C or D
                if signed and i == len(s) - 1:
                    if number >= 0:
                        val = 0xC0 + int(digit)
                    else:
                        val = 0xD0 + int(digit)
                encoded.append(val)
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '08')
        
        # Date: 19991231
        set_zoned(10, 19991231, 8) 
        
        # Acres Per Unit: 40.50 (PIC 9(04)V99 -> 6 digits)
        # Value 4050 -> 004050
        set_zoned(46, 4050, 6)
        
        parsed = self.parser.parse_record(bytes(record), GSFLDRUL_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '08')
        self.assertEqual(parsed['FL_GAS_PRORATION_EFF_DATE'], 19991231)
        self.assertEqual(parsed['FL_GAS_ACRES_PER-UNIT'], 40.50)

    def test_gasaform_parsing(self):
        # 09 GASAFORM
        from rrc_fields.layouts import GASAFORM_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, signed=False):
            # Simple unsigned zoned
            s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '09')
        # Factor Codes (01)
        set_ebcdic(5, '01') 
        # Percent (9V99) e.g. 50% = 5.00? or 50.00? 
        # Layout: 9V99 -> 3 digits. 50% -> 050 (0.50) or 500 (5.00). 
        # Assuming RRC data convention: 3 digits implies 050 = .50 or 50%? 
        # Standard: 9V99 = 1.23. 500 = 5.00. 
        # Let's test basic decimal parsing. 123 -> 1.23
        set_zoned(2, 123, 3) 
        
        parsed = self.parser.parse_record(bytes(record), GASAFORM_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '09')
        self.assertEqual(parsed['FL_GAS_ALLOW_PERCENT_FACTR'], 1.23)
        self.assertEqual(parsed['FL_GAS_ALLOCATION_FCTR_CD'], '01')

    def test_value_conversion(self):
        # Verify 01 maps to % DELIVERABILITY
        from rrc_fields.layouts import GASAFORM_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        set_ebcdic(0, '09')
        set_ebcdic(5, '01') 
        
        # Parse w/ conversion
        parsed = self.parser.parse_record(bytes(record), GASAFORM_LAYOUT, convert_values=True)
        self.assertEqual(parsed['FL_GAS_ALLOCATION_FCTR_CD'], '% DELIVERABILITY')

    def test_parser_filtering(self):
        # Functional test of filtering logic using mocks would be better in test_parser,
        # but here we can partial check if included
        pass

    def test_gasrmrks_parsing(self):
        # 10 GASRMRKS
        from rrc_fields.layouts import GASRMRKS_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, signed=False):
            # Simple unsigned zoned
            s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '10')
        # Remark Num 100
        set_zoned(2, 100, 3) 
        # Text
        set_ebcdic(21, 'Test Remark Line.')

        parsed = self.parser.parse_record(bytes(record), GASRMRKS_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '10')
        self.assertEqual(parsed['FL_GAS_REMARK_NUMBER'], 100)
        self.assertEqual(parsed['FL_GAS_REMARK_TEXT'].strip(), 'Test Remark Line.')

    def test_gscounty_parsing(self):
        # 11 GSCOUNTY
        from rrc_fields.layouts import GSCOUNTY_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, signed=False):
            # Simple unsigned zoned
            s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '11')
        # County Code (e.g. 123)
        set_zoned(2, 123, 3) 

        parsed = self.parser.parse_record(bytes(record), GSCOUNTY_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '11')
        self.assertEqual(parsed['FL_GAS_COUNTY_CODE'], 123)

    def test_gasafact_parsing(self):
        # 12 GASAFACT
        from rrc_fields.layouts import GASAFACT_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length):
            s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)
            
        def set_packed(start, number, length, scale=0):
            # Duplicate set_packed logic
            s = str(abs(int(number * (10**scale))))
            if len(s) % 2 == 0:
                s = '0' + s 
            digits = [int(ch) for ch in s]
            target_nibbles = length * 2
            current_nibbles = len(digits) + 1 
            padding = target_nibbles - current_nibbles
            nibbles = [0] * padding + digits
            sign = 0xC if number >= 0 else 0xD
            nibbles.append(sign)
            packed_bytes = bytearray()
            for i in range(0, len(nibbles), 2):
                byte = (nibbles[i] << 4) | nibbles[i+1]
                packed_bytes.append(byte)
            record[start:start+len(packed_bytes)] = packed_bytes

        # ID
        set_ebcdic(0, '12')
        # Code 1 = 17 (ACRES X SHUT-IN WELL PRESSURE)
        set_ebcdic(6, '17')
        # Factor 1 = 0.1234567
        set_packed(8, 0.1234567, 8, scale=7)
        # Verify 5th Offset: Code 5 at 46, Factor 5 at 48
        set_ebcdic(46, '06')
        set_packed(48, 100.0, 8, scale=7)

        parsed = self.parser.parse_record(bytes(record), GASAFACT_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '12')
        self.assertEqual(parsed['FL_FACTOR_CODE_1'], '17')
        self.assertAlmostEqual(parsed['FL_GAS_ALLOCATION_FACTOR_1'], 0.1234567)
        self.assertEqual(parsed['FL_FACTOR_CODE_5'], '06')
        self.assertAlmostEqual(parsed['FL_GAS_ALLOCATION_FACTOR_5'], 100.0)

        # Check Conversion
        parsed_conv = self.parser.parse_record(bytes(record), GASAFACT_LAYOUT, convert_values=True)
        self.assertEqual(parsed_conv['FL_FACTOR_CODE_1'], 'ACRES X SHUT-IN WELL PRESSURE')

    def test_asheet_parsing(self):
        # 13 ASHEET
        from rrc_fields.layouts import ASHEET_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length):
            s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)
            
        def set_packed(start, number, length, scale=0):
            # Duplicate set_packed logic logic
            # For scale=0, number is int
            s = str(abs(int(number)))
            if len(s) % 2 == 0:
                s = '0' + s 
            digits = [int(ch) for ch in s]
            target_nibbles = length * 2
            current_nibbles = len(digits) + 1 
            padding = target_nibbles - current_nibbles
            nibbles = [0] * padding + digits
            sign = 0xC if number >= 0 else 0xD
            nibbles.append(sign)
            packed_bytes = bytearray()
            for i in range(0, len(nibbles), 2):
                byte = (nibbles[i] << 4) | nibbles[i+1]
                packed_bytes.append(byte)
            record[start:start+len(packed_bytes)] = packed_bytes

        # ID
        set_ebcdic(0, '13')
        # Balance Period Date: 2025-06
        set_zoned(2, 20, 2)
        set_zoned(4, 25, 2)
        set_zoned(6, 6, 2)
        # Current 6mo Status: -123456
        set_packed(10, -123456, 5)
        # Page Num
        set_zoned(47, 42, 4)

        parsed = self.parser.parse_record(bytes(record), ASHEET_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '13')
        self.assertEqual(parsed['FL_AS_BALANCING_PERIOD_CENT'], 20)
        self.assertEqual(parsed['FL_AS_BALANCING_PERIOD_YEAR'], 25)
        self.assertEqual(parsed['FL_AS_BALANCING_PERIOD_MONTH'], 6)
        self.assertEqual(parsed['FL_AS_CURRENT_6MO_STATUS'], -123456)
        self.assertEqual(parsed['FL_AS_PAGE_NUMBER'], 42)

    def test_asheetmo_parsing(self):
        # 14 ASHEETMO
        from rrc_fields.layouts import ASHEETMO_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length):
            s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)
            
        def set_packed(start, number, length, scale=0):
            # Duplicate set_packed logic logic
            s = str(abs(int(number)))
            if len(s) % 2 == 0:
                s = '0' + s 
            digits = [int(ch) for ch in s]
            target_nibbles = length * 2
            current_nibbles = len(digits) + 1 
            padding = target_nibbles - current_nibbles
            nibbles = [0] * padding + digits
            sign = 0xC if number >= 0 else 0xD
            nibbles.append(sign)
            packed_bytes = bytearray()
            for i in range(0, len(nibbles), 2):
                byte = (nibbles[i] << 4) | nibbles[i+1]
                packed_bytes.append(byte)
            record[start:start+len(packed_bytes)] = packed_bytes

        # ID
        set_ebcdic(0, '14')
        # Sched Date: 202506
        set_zoned(2, 20, 2)
        set_zoned(4, 25, 2)
        set_zoned(6, 6, 2)
        
        # Current Forecast 11-16 (5 bytes)
        set_packed(10, 500000, 5)
        
        # Extra Adj 56-60 (4 bytes)
        set_packed(55, 12345, 4)

        # Max Deliv 141-146 (5 bytes) -> Pos 141-146 is 90-95 relative to record? NO field list says Pos 141
        # Layout index: start 140
        set_packed(140, 999999, 5)
        
        # Flag at 88
        set_ebcdic(88, 'Y')

        parsed = self.parser.parse_record(bytes(record), ASHEETMO_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '14')
        self.assertEqual(parsed['FL_AS_SCHED_CENTURY'], 20)
        self.assertEqual(parsed['FL_AS_SCHED_MONTH'], 6)
        self.assertEqual(parsed['FL_AS_CURRENT_FORECAST'], 500000)
        self.assertEqual(parsed['FL_AS_EXTRA_ADJUSTMENT'], 12345)
        self.assertEqual(parsed['FL_AS_MAX_DELIV'], 999999)
        self.assertEqual(parsed['FL_AS_FIELD_BALANCED_FLAG'], 'Y')

    def test_flt3root_parsing(self):
        # 15 FLT3ROOT
        from rrc_fields.layouts import FLT3ROOT_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length):
            s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '15')
        # Nominator Number 123456
        set_zoned(2, 123456, 6)
        # System Number 7890
        set_zoned(8, 7890, 4)

        parsed = self.parser.parse_record(bytes(record), FLT3ROOT_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '15')
        self.assertEqual(parsed['FL_T3_NOMINATOR_NUMBER'], 123456)
        self.assertEqual(parsed['FL_T3_SYSTEM_NUMBER'], 7890)

    def test_fldt3_parsing(self):
        # 16 FLDT3
        from rrc_fields.layouts import FLDT3_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            # Scale simply treats input as int for zoned string purposes if scale > 0
            # E.g. 50.00 scale 2 -> "5000"
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
                
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '16')
        # Report Date: 202512
        set_zoned(2, 202512, 6)
        # Percentage 50.00% -> 0.50 (PIC 9V99 fits 0.50 as 050, 50.00 as 5000 overflows)
        set_zoned(9, 0.50, 3, scale=2) 
        # Amount of Gas: 987654321
        set_zoned(21, 987654321, 9)

        parsed = self.parser.parse_record(bytes(record), FLDT3_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '16')
        self.assertEqual(parsed['FL_T3_REPORT_YEAR'], 25)
        self.assertAlmostEqual(parsed['FL_T3_PERC_FLD_DEL'], 0.50)
        self.assertEqual(parsed['FL_T3_AMOUNT_OF_GAS'], 987654321)

    def test_fldmo_parsing(self):
        # 17 FLDMO
        from rrc_fields.layouts import FLDMO_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        def set_packed(start, number, length, scale=0):
            # Duplicate set_packed logic logic
            s = str(abs(int(number)))
            if len(s) % 2 == 0:
                s = '0' + s 
            digits = [int(ch) for ch in s]
            target_nibbles = length * 2
            current_nibbles = len(digits) + 1 
            padding = target_nibbles - current_nibbles
            nibbles = [0] * padding + digits
            sign = 0xC if number >= 0 else 0xD
            nibbles.append(sign)
            packed_bytes = bytearray()
            for i in range(0, len(nibbles), 2):
                byte = (nibbles[i] << 4) | nibbles[i+1]
                packed_bytes.append(byte)
            record[start:start+len(packed_bytes)] = packed_bytes

        # ID
        set_ebcdic(0, '17')
        # Date 202410
        set_zoned(2, 202410, 6)
        
        # Gas Allowable (7 bytes)
        set_packed(10, 1000000, 7)
        # Liquid Cond Allowable (5 bytes)
        set_packed(17, 5000, 5)
        # Partial Gas Well Flag
        set_ebcdic(42, 'A')
        # Last Updated 20241101
        set_zoned(54, 20241101, 8)

        parsed = self.parser.parse_record(bytes(record), FLDMO_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '17')
        self.assertEqual(parsed['FL_PRODUCTION_CENTURY'], 20)
        self.assertEqual(parsed['FL_PRODUCTION_YEAR'], 24)
        self.assertEqual(parsed['FL_PRODUCTION_MONTH'], 10)
        self.assertEqual(parsed['FL_GAS_ALLOWABLE'], 1000000)
        self.assertEqual(parsed['FL_LIQUID_COND_ALLOWABLE'], 5000)
        self.assertEqual(parsed['FL_PARTIAL_GAS_WELL_PROD_CD'], 'A')
        self.assertEqual(parsed['FL_MONTH_LAST_UPDATED'], 11)

    def test_calc49b_parsing(self):
        # 18 CALC49B
        from rrc_fields.layouts import CALC49B_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        def set_packed(start, number, length, scale=0):
            # Duplicate set_packed logic logic
            s = str(abs(int(number)))
            if len(s) % 2 == 0:
                s = '0' + s 
            digits = [int(ch) for ch in s]
            target_nibbles = length * 2
            current_nibbles = len(digits) + 1 
            padding = target_nibbles - current_nibbles
            nibbles = [0] * padding + digits
            sign = 0xC if number >= 0 else 0xD
            nibbles.append(sign)
            packed_bytes = bytearray()
            for i in range(0, len(nibbles), 2):
                byte = (nibbles[i] << 4) | nibbles[i+1]
                packed_bytes.append(byte)
            record[start:start+len(packed_bytes)] = packed_bytes

        # ID
        set_ebcdic(0, '18')
        # Date 20241231
        set_zoned(2, 20241231, 8)
        # Gas Gravity 0.650 (PIC V999)
        set_zoned(18, 0.650, 3, scale=3)
        # Formation Vol Factor 1.2500 (PIC 9V9(04))
        set_zoned(29, 1.2500, 5, scale=4)
        # Solution GOR 1000.5000 (PIC 9(05)V9(04))
        set_zoned(34, 1000.5000, 9, scale=4) 
        # Deviation Factor 0.9800 (PIC 9V9(04))
        set_zoned(43, 0.9800, 5, scale=4)
        # Daily Allow Cub Ft (6 bytes packed)
        set_packed(48, 12345678901, 6) # PIC 9(11)

        parsed = self.parser.parse_record(bytes(record), CALC49B_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '18')
        self.assertEqual(parsed['FL_GAS_ALLOW_EFFECTIVE_CC'], 20)
        self.assertEqual(parsed['FL_GAS_ALLOW_EFFECTIVE_YY'], 24)
        self.assertAlmostEqual(parsed['FL_G_1_GAS_GRAVITY'], 0.650)
        self.assertAlmostEqual(parsed['FL_FORMATION_VOLUME_FACTOR'], 1.2500)
        self.assertAlmostEqual(parsed['FL_SOLUTION_GAS_OIL_RATIO'], 1000.5000)
        self.assertAlmostEqual(parsed['FL_DEVIATION_FACTOR'], 0.9800)
        self.assertEqual(parsed['FL_TOP_DAILY_GAS_ALLOW_CU_FT'], 12345678901)

    def test_oilseg_parsing(self):
        # 19 OILSEG
        from rrc_fields.layouts import OILSEG_LAYOUT
        record = bytearray([0x40] * 300)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        def set_packed(start, number, length, scale=0):
            s = str(abs(int(number)))
            if len(s) % 2 == 0:
                s = '0' + s 
            digits = [int(ch) for ch in s]
            target_nibbles = length * 2
            current_nibbles = len(digits) + 1 
            padding = target_nibbles - current_nibbles
            nibbles = [0] * padding + digits
            sign = 0xC if number >= 0 else 0xD
            nibbles.append(sign)
            packed_bytes = bytearray()
            for i in range(0, len(nibbles), 2):
                byte = (nibbles[i] << 4) | nibbles[i+1]
                packed_bytes.append(byte)
            record[start:start+len(packed_bytes)] = packed_bytes

        # ID
        set_ebcdic(0, '19')
        # Key 'O'
        set_ebcdic(2, 'O')
        # Discovery Date 19500101
        set_zoned(3, 19500101, 8)
        # Offshore Code "SO"
        set_ebcdic(26, 'SO')
        # Cum Oil Prod (7 bytes packed) pos 29
        set_packed(29, 1234567890123, 7)
        # New Field Approval Date
        set_zoned(164, 20241231, 8)

        parsed = self.parser.parse_record(bytes(record), OILSEG_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '19')
        self.assertEqual(parsed['FL_OILSEG_KEY'], 'O')
        self.assertEqual(parsed['FL_OIL_DISC_YEAR'], 50)
        self.assertEqual(parsed['FL_OIL_OFFSHORE_CODE'], 'SO')
        self.assertEqual(parsed['FL_CUM_OIL_PRODUCTION_TO_CONV'], 1234567890123)
        self.assertEqual(parsed['FL_NEW_FLD_APPRVL_CC'], 20)
        self.assertEqual(parsed['FL_NEW_FLD_APPRVL_YR'], 24)

    def test_oilcycle_parsing(self):
        # 20 OILCYCLE
        from rrc_fields.layouts import OILCYCLE_LAYOUT
        record = bytearray([0x40] * 240)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        def set_packed(start, number, length, scale=0):
            s = str(abs(int(number)))
            if len(s) % 2 == 0:
                s = '0' + s 
            digits = [int(ch) for ch in s]
            target_nibbles = length * 2
            current_nibbles = len(digits) + 1 
            padding = target_nibbles - current_nibbles
            nibbles = [0] * padding + digits
            sign = 0xC if number >= 0 else 0xD
            nibbles.append(sign)
            packed_bytes = bytearray()
            for i in range(0, len(nibbles), 2):
                byte = (nibbles[i] << 4) | nibbles[i+1]
                packed_bytes.append(byte)
            record[start:start+len(packed_bytes)] = packed_bytes

        # ID
        set_ebcdic(0, '20')
        # Key 1234
        set_zoned(2, 1234, 4)
        # Type Code 'R'
        set_ebcdic(6, 'R')
        # Top Allowable Amt (4 bytes packed)
        set_packed(10, 500000, 4)
        # Regular Flag
        set_ebcdic(18, 'Y')

        parsed = self.parser.parse_record(bytes(record), OILCYCLE_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '20')
        self.assertEqual(parsed['FL_OIL_CYCLE_KEY'], 1234)
        self.assertEqual(parsed['FL_OIL_TYPE_FIELD_CODE'], 'R')
        self.assertEqual(parsed['FL_OIL_TOP_ALLOWABLE_AMT'], 500000)
        self.assertEqual(parsed['FL_OIL_COUNTY_REGULAR_FLAG'], 'Y')

    def test_olfldrul_parsing(self):
        # 21 OLFLDRUL
        from rrc_fields.layouts import OLFLDRUL_LAYOUT
        record = bytearray([0x40] * 300)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '21')
        # Proration Eff Date 20250101
        set_zoned(10, 20250101, 8)
        # Spacing to Line 467
        set_zoned(37, 467, 4)
        # Spacing to Well 1200
        set_zoned(41, 1200, 4)
        # Acres per Unit 40.00 (PIC 9(04)V99 -> 6 digits, scale 2)
        set_zoned(45, 40.00, 6, scale=2)
        # Tolerance Acres 5.50 (PIC 9(03)V99 -> 5 digits, scale 2)
        set_zoned(52, 5.50, 5, scale=2)
        # Docket Number
        set_ebcdic(184, '0123456789')
        # Not Reliable Flag
        set_ebcdic(194, 'Y')

        parsed = self.parser.parse_record(bytes(record), OLFLDRUL_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '21')
        self.assertEqual(parsed['FL_OIL_PRORATION_EFF_CENTURY'], 20)
        self.assertEqual(parsed['FL_OIL_SPACING_TO_LEASE_LINE'], 467)
        self.assertEqual(parsed['FL_OIL_SPACING_TO_WELL'], 1200)
        self.assertAlmostEqual(parsed['FL_OIL_ACRES_PER_UNIT'], 40.00)
        self.assertAlmostEqual(parsed['FL_OIL_TOLERANCE_ACRES'], 5.50)
        self.assertEqual(parsed['FL_OIL_DOCKET_NUMBER'], '0123456789')
        self.assertEqual(parsed['FL_OIL_DOCKET_NUMBER'], '0123456789')
        self.assertEqual(parsed['FL_OIL_RULES_NOT_RELIABLE_FLAG'], 'Y')

    def test_oilaform_parsing(self):
        # 22 OILAFORM
        from rrc_fields.layouts import OILAFORM_LAYOUT, OIL_ALLOCATION_FACTOR_LOOKUP
        record = bytearray([0x40] * 50)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '22')
        # Percent Factor 50.00% (PIC 9V99 -> 500)
        set_zoned(2, 5.00, 3, scale=2)
        # Factor Code '02' (ACRES)
        set_zoned(5, 2, 2)

        parsed = self.parser.parse_record(bytes(record), OILAFORM_LAYOUT, convert_values=True)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '22')
        self.assertAlmostEqual(parsed['FL_OIL_ALLOW_PERCENT_FACTOR'], 5.00)
        self.assertAlmostEqual(parsed['FL_OIL_ALLOW_PERCENT_FACTOR'], 5.00)
        self.assertEqual(parsed['FL_OIL_ALLOCATION_FCTR_CODE'], 'ACRES')

    def test_oilrmrks_parsing(self):
        # 23 OILRMRKS
        from rrc_fields.layouts import OILRMRKS_LAYOUT
        record = bytearray([0x40] * 100)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '23')
        # Remark Number 123
        set_zoned(2, 123, 3)
        # Line Number 1
        set_zoned(5, 1, 3)
        # Flags
        set_ebcdic(8, 'Y') # Annual
        set_ebcdic(9, 'N') # Ledger
        set_ebcdic(20, 'THIS IS A REMARK TEST')

        parsed = self.parser.parse_record(bytes(record), OILRMRKS_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '23')
        self.assertEqual(parsed['FL_OIL_REMARK_NUMBER'], 123)
        self.assertEqual(parsed['FL_OIL_REMARK_LINE_NO'], 1)
        self.assertEqual(parsed['FL_OIL_PRINT_ANNUAL_FLAG'], 'Y')
        self.assertEqual(parsed['FL_OIL_PRINT_LEDGER_FLAG'], 'N')
        self.assertEqual(parsed['FL_OIL_PRINT_LEDGER_FLAG'], 'N')
        self.assertEqual(parsed['FL_OIL_REMARK_TEXT'], 'THIS IS A REMARK TEST')

    def test_oilftrot_parsing(self):
        # 24 OILFTROT
        from rrc_fields.layouts import OILFTROT_LAYOUT
        record = bytearray([0x40] * 50)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        def set_packed(start, number, length, scale=0):
            s = str(abs(int(number * (10**scale))))
            if len(s) % 2 == 0:
                s = '0' + s 
            digits = [int(ch) for ch in s]
            target_nibbles = length * 2
            current_nibbles = len(digits) + 1 
            padding = target_nibbles - current_nibbles
            nibbles = [0] * padding + digits
            sign = 0xC if number >= 0 else 0xD
            nibbles.append(sign)
            packed_bytes = bytearray()
            for i in range(0, len(nibbles), 2):
                byte = (nibbles[i] << 4) | nibbles[i+1]
                packed_bytes.append(byte)
            record[start:start+len(packed_bytes)] = packed_bytes

        # ID
        set_ebcdic(0, '24')
        # Key 2025
        set_zoned(2, 2025, 4)
        # Exempt Flag 'N'
        set_ebcdic(6, 'N')
        # Prod Factor 1.1234567 (PIC S9(8)V9(7) -> 15 digits -> 1.1234567)
        # 11234567 in packed? No, scale is 7. So integer rep is 11234567
        # Wait, PIC S9(8)V9(7). Total 15 digits.
        # 1.1234567 -> 11234567.
        set_packed(7, 1.1234567, 8, scale=7)
        
        # Split Prod Factor
        set_packed(15, 0.5000000, 8, scale=7)
        
        # Split Date 15
        set_zoned(23, 15, 2)

        parsed = self.parser.parse_record(bytes(record), OILFTROT_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '24')
        self.assertEqual(parsed['FL_OIL_FACTOR_CYCLE_KEY'], 2025)
        self.assertEqual(parsed['FL_OIL_PROD_FACT_EXEMPT_FLAG'], 'N')
        self.assertAlmostEqual(parsed['FL_OIL_PROD_FACTOR'], 1.1234567)
        self.assertAlmostEqual(parsed['FL_OIL_SPLIT_PROD_FACTOR'], 0.5000000)
        self.assertAlmostEqual(parsed['FL_OIL_SPLIT_PROD_FACTOR'], 0.5000000)
        self.assertEqual(parsed['FL_OIL_SPLIT_PROD_FACTOR_DATE'], 15)

    def test_oilafact_parsing(self):
        # 25 OILAFACT
        from rrc_fields.layouts import OILAFACT_LAYOUT
        record = bytearray([0x40] * 50)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        def set_packed(start, number, length, scale=0):
            s = str(abs(int(number * (10**scale))))
            if len(s) % 2 == 0:
                s = '0' + s 
            digits = [int(ch) for ch in s]
            target_nibbles = length * 2
            current_nibbles = len(digits) + 1 
            padding = target_nibbles - current_nibbles
            nibbles = [0] * padding + digits
            sign = 0xC if number >= 0 else 0xD
            nibbles.append(sign)
            packed_bytes = bytearray()
            for i in range(0, len(nibbles), 2):
                byte = (nibbles[i] << 4) | nibbles[i+1]
                packed_bytes.append(byte)
            record[start:start+len(packed_bytes)] = packed_bytes

        # ID
        set_ebcdic(0, '25')
        # Factor Code '14' (ORIGINAL OIL IN PLACE)
        set_zoned(2, 14, 2)
        # Factor 0.1234567
        set_packed(4, 0.1234567, 8, scale=7)

        parsed = self.parser.parse_record(bytes(record), OILAFACT_LAYOUT, convert_values=True)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '25')
        self.assertEqual(parsed['FL_OIL_FACTOR_CODE'], 'ORIGINAL OIL IN PLACE')
        self.assertAlmostEqual(parsed['FL_OIL_ALLOCATION_FACTOR'], 0.1234567)

    def test_olcounty_parsing(self):
        # 26 OLCOUNTY
        from rrc_fields.layouts import OLCOUNTY_LAYOUT
        record = bytearray([0x40] * 20)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '26')
        # County Code 123
        set_zoned(2, 123, 3)

        parsed = self.parser.parse_record(bytes(record), OLCOUNTY_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '26')
        self.assertEqual(parsed['FL_OIL_COUNTY_CODE'], 123)

    def test_assocgas_parsing(self):
        # 27 ASSOCGAS
        from rrc_fields.layouts import ASSOCGAS_LAYOUT
        record = bytearray([0x40] * 20)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '27')
        # District Code '07' -> '6E' in lookup
        set_zoned(2, 7, 2) 
        # Field Number 98765432
        set_zoned(4, 98765432, 8)

        parsed = self.parser.parse_record(bytes(record), ASSOCGAS_LAYOUT, convert_values=True)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '27')
        # Check lookup value '07' -> '6E'
        self.assertEqual(parsed['FL_ASSOC_GAS_FIELD_DIST'], '6E')
        self.assertEqual(parsed['FL_ASSOC_GAS_FIELD_NUMBER'], 98765432)

    def test_fldmap_parsing(self):
        # 28 FLDMAP
        from rrc_fields.layouts import FLDMAP_LAYOUT
        record = bytearray([0x40] * 50)
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '28')
        # Map Index 'MAP123'
        set_ebcdic(2, 'MAP123')
        # County Codes
        set_ebcdic(8, '456')
        set_ebcdic(11, '789')
        set_ebcdic(14, '012')

        parsed = self.parser.parse_record(bytes(record), FLDMAP_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '28')
        self.assertEqual(parsed['FL_MAP_NUMBER_INDEX'], 'MAP123')
        self.assertEqual(parsed['FL_MAP_COUNTY_CODE_1'], '456')
        self.assertEqual(parsed['FL_MAP_COUNTY_CODE_2'], '789')
        self.assertEqual(parsed['FL_MAP_COUNTY_CODE_3'], '012')
        # Check defaults (0x40 EBCDIC space -> Unicode space)
        self.assertEqual(parsed['FL_MAP_COUNTY_CODE_6'].strip(), '')

    def test_gsoptrul_parsing(self):
        # 29 GSOPTRUL
        from rrc_fields.layouts import GSOPTRUL_LAYOUT
        record = bytearray([0x40] * 80) # 75 bytes
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '29')
        # Space to lease line: 467
        set_zoned(4, 467, 4)
        # Acres per unit: 40.00 (scale 2)
        set_zoned(12, 40.00, 6, scale=2)
        # Tolerance acres: 1.50 (scale 2)
        set_zoned(18, 1.50, 5, scale=2)
        # Diagonal Code CC
        set_ebcdic(23, 'CC')
        # Diagonal Feet 2000
        set_zoned(25, 2000, 5)

        parsed = self.parser.parse_record(bytes(record), GSOPTRUL_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '29')
        self.assertEqual(parsed['FL_GAS_OPT_SPACE_TO_LEASE_LINE'], 467)
        self.assertAlmostEqual(parsed['FL_GAS_OPT_ACRES_PER_UNIT'], 40.0)
        self.assertAlmostEqual(parsed['FL_GAS_OPT_TOLERANCE_ACRES'], 1.5)
        self.assertEqual(parsed['FL_GAS_OPT_DIAGONAL_CODE'], 'CC')
        self.assertEqual(parsed['FL_GAS_OPT_DIAGONAL_FEET'], 2000)

    def test_oloptrul_parsing(self):
        # 30 OLOPTRUL (Structure mirrors GSOPTRUL)
        from rrc_fields.layouts import OLOPTRUL_LAYOUT
        record = bytearray([0x40] * 80) # 75 bytes
        
        def set_ebcdic(start, text):
            b = codecs.encode(text, 'cp037')
            record[start:start+len(b)] = b
            
        def set_zoned(start, number, length, scale=0):
            if scale > 0:
                s = str(int(number * (10**scale))).zfill(length)
            else:
                s = str(abs(number)).zfill(length)
            encoded = []
            for digit in s:
                encoded.append(0xF0 + int(digit))
            record[start:start+len(encoded)] = bytes(encoded)

        # ID
        set_ebcdic(0, '30')
        # Space to lease line: 330
        set_zoned(4, 330, 4)
        # Acres per unit: 20.00 (scale 2)
        set_zoned(12, 20.00, 6, scale=2)
        # Tolerance acres: 2.50 (scale 2)
        set_zoned(18, 2.50, 5, scale=2)
        # Diagonal Code WC
        set_ebcdic(23, 'WC')
        # Diagonal Feet 1500
        set_zoned(25, 1500, 5)

        parsed = self.parser.parse_record(bytes(record), OLOPTRUL_LAYOUT)
        
        self.assertEqual(parsed['RRC_TAPE_RECORD_ID'], '30')
        self.assertEqual(parsed['FL_OIL_OPT_SPACE_TO_LEASE_LINE'], 330)
        self.assertAlmostEqual(parsed['FL_OIL_OPT_ACRES_PER_UNIT'], 20.0)
        self.assertAlmostEqual(parsed['FL_OIL_OPT_TOLERANCE_ACRES'], 2.5)
        self.assertEqual(parsed['FL_OIL_OPT_DIAGONAL_CODE'], 'WC')
        self.assertEqual(parsed['FL_OIL_OPT_DIAGONAL_FEET'], 1500)

if __name__ == '__main__':
    unittest.main()
