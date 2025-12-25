import unittest
import codecs
from rrc_fields import RRCFieldParser

class TestRRCFieldParser(unittest.TestCase):
    def setUp(self):
        self.parser = RRCFieldParser(encoding='cp037')

    def test_unpack_comp3_positive(self):
        # 12345 C -> 123.45 (scale=2)
        # Hex: 12 34 5C
        data = bytes.fromhex('12345C')
        value = self.parser.unpack_comp3(data, scale=2)
        self.assertEqual(value, 123.45)

    def test_unpack_comp3_negative(self):
         # 12345 D -> -123.45 (scale=2)
        # Hex: 12 34 5D
        data = bytes.fromhex('12345D')
        value = self.parser.unpack_comp3(data, scale=2)
        self.assertEqual(value, -123.45)
        
    def test_unpack_comp3_no_scale(self):
        # 999 F -> 999
        # Hex: 99 9F
        data = bytes.fromhex('999F')
        value = self.parser.unpack_comp3(data, scale=0)
        self.assertEqual(value, 999)

    def test_parse_record_string(self):
        # "TEST" in cp037 EBCDIC
        ebcdic_str = codecs.encode("TEST", 'cp037')
        layout = [{'name': 'field1', 'start': 0, 'length': 4, 'type': 'string'}]
        result = self.parser.parse_record(ebcdic_str, layout)
        self.assertEqual(result['field1'], "TEST")

    def test_parse_record_mixed(self):
        # Field 1: "A" (EBCDIC C1)
        # Field 2: 123C (Packed 123, scale 0) -> Hex: 12 3C
        
        # Construct record: C1 12 3C
        record = bytes.fromhex('C1123C')
        
        layout = [
            {'name': 'char_field', 'start': 0, 'length': 1, 'type': 'string'},
            {'name': 'num_field', 'start': 1, 'length': 2, 'type': 'packed', 'scale': 0}
        ]
        
        result = self.parser.parse_record(record, layout)
        self.assertEqual(result['char_field'], "A")
        self.assertEqual(result['num_field'], 123)

    def test_unpack_zoned_unsigned(self):
        # 12345 (F1 F2 F3 F4 F5) -> 12345
        data = bytes.fromhex('F1F2F3F4F5')
        value = self.parser.unpack_zoned(data)
        self.assertEqual(value, 12345)
        
    def test_unpack_zoned_signed_positive(self):
        # 12345 (F1 F2 F3 F4 C5) -> 12345
        data = bytes.fromhex('F1F2F3F4C5')
        value = self.parser.unpack_zoned(data)
        self.assertEqual(value, 12345)

    def test_unpack_zoned_signed_negative(self):
        # -12345 (F1 F2 F3 F4 D5) -> -12345
        data = bytes.fromhex('F1F2F3F4D5')
        value = self.parser.unpack_zoned(data)
        self.assertEqual(value, -12345)
        
    def test_unpack_zoned_scale(self):
        # -123.45 (scale 2) -> F1 F2 F3 F4 D5
        data = bytes.fromhex('F1F2F3F4D5')
        value = self.parser.unpack_zoned(data, scale=2)
        self.assertEqual(value, -123.45)

if __name__ == '__main__':
    unittest.main()
