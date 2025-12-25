import codecs
import struct
from .layouts import get_layout

class RRCFieldParser:
    def __init__(self, encoding='cp037'):
        """
        Initialize the parser with the specified EBCDIC encoding.
        Common encodings: 'cp037' (US EBCDIC), 'cp500' (International EBCDIC).
        """
        self.encoding = encoding

    @staticmethod
    def unpack_zoned(byte_data, scale=0):
        """
        Unpack EBCDIC Zoned Decimal data.
        
        Args:
            byte_data (bytes): The bytes containing the zoned decimal.
            scale (int): Number of decimal places.
            
        Returns:
            float: The unpacked number.
        """
        if not byte_data:
            return 0.0

        # EBCDIC Zoned Decimal:
        # Digits 0-9 are 0xF0-0xF9
        # Sign is in the zone (upper nibble) of the last byte.
        # F, C, A, E = positive
        # D, B = negative
        
        # We need to convert the EBCDIC bytes to ASCII digits first
        # But handle the last byte specially for sign.
        
        digits = []
        sign_multiplier = 1
        
        for i, byte in enumerate(byte_data):
            upper_nibble = (byte >> 4) & 0x0F
            lower_nibble = byte & 0x0F
            
            if i == len(byte_data) - 1:
                # Last byte contains sign in upper nibble
                if upper_nibble in (0xD, 0xB):
                    sign_multiplier = -1
                # Lower nibble is the digit
                digits.append(str(lower_nibble))
            else:
                # Standard digit, upper nibble usually F
                digits.append(str(lower_nibble))
                
        value_str = "".join(digits)
        try:
            value = int(value_str)
        except ValueError:
            return 0.0
            
        value = value * sign_multiplier
        
        if scale > 0:
            value = value / (10 ** scale)
            
        return value

    @staticmethod
    def unpack_comp3(byte_data, scale=0):
        """
        Unpack EBCDIC COMP-3 (packed decimal) data.
        
        Args:
            byte_data (bytes): The bytes containing the packed decimal.
            scale (int): Number of decimal places.
            
        Returns:
            float: The unpacked number.
        """
        hex_str = byte_data.hex()
        if not hex_str:
            return 0.0

        # The last nibble is the sign
        # C, A, F, E = positive
        # D, B = negative
        sign_nibble = hex_str[-1].upper()
        value_str = hex_str[:-1]
        
        try:
            value = int(value_str)
        except ValueError:
            return 0.0
        
        if sign_nibble in ('D', 'B'):
            value = -value
            
        if scale > 0:
            value = value / (10 ** scale)
            
        return value

    def parse_record(self, record_bytes, layout, convert_values=False):
        """
        Parse a single record based on the provided layout.
        
        Args:
            record_bytes (bytes): The raw bytes of the record.
            layout (list of dict): Definition of fields. 
                Each dict should have: 'name', 'start', 'length', 'type', 'scale' (optional for packed).
                Start is 0-indexed.
            convert_values(bool): If True, use 'lookup' maps to convert codes to labels.
            
        Returns:
            dict: Parsed field values.
        """
        parsed_data = {}
        for field in layout:
            start = field['start']
            length = field['length']
            end = start + length
            field_bytes = record_bytes[start:end]
            
            field_type = field.get('type', 'string')
            scale = field.get('scale', 0)
            
            if field_type == 'packed':
                parsed_data[field['name']] = self.unpack_comp3(field_bytes, scale)
            elif field_type == 'zoned':
                parsed_data[field['name']] = self.unpack_zoned(field_bytes, scale)
            elif field_type == 'int':
                 # Assuming binary integer (big-endian)
                if length == 2:
                    parsed_data[field['name']] = struct.unpack('>h', field_bytes)[0]
                elif length == 4:
                    parsed_data[field['name']] = struct.unpack('>i', field_bytes)[0]
                else:
                    # Fallback or specific handling for other sizes
                    try:
                        parsed_data[field['name']] = int(codecs.decode(field_bytes, self.encoding))
                    except ValueError:
                         parsed_data[field['name']] = 0
            else: # defaults to string
                try:
                    value = codecs.decode(field_bytes, self.encoding).strip()
                except UnicodeDecodeError:
                     # Fallback for transient decode errors, replace valid chars
                     value = codecs.decode(field_bytes, self.encoding, errors='replace').strip()
                parsed_data[field['name']] = value

            # Apply lookup if enabled
            if convert_values and 'lookup' in field and parsed_data[field['name']] in field['lookup']:
                parsed_data[field['name']] = field['lookup'][parsed_data[field['name']]]

        return parsed_data

    def parse_file(self, file_path, record_length=240, include=None, convert_values=False, layout=None):
        """
        Parse a fixed-width EBCDIC file.
        
        Args:
            file_path (str): Path to the .ebc file.
            record_length (int): Fixed length of each record in bytes. Defaults to 240.
            include (list, optional): List of Record IDs ('01', 'GASSEG') to parse. 
                If None/Empty, parses all records that have a defined layout.
            convert_values (bool): If True, convert codes to descriptions using layout lookups.
            layout: 
                - None (default): Uses internal get_layout registry.
                - A list of dicts (Single layout mode)
                - A function/callable (Multi-record mode). Accepts record_bytes, returns layout list or None.
            
        Yields:
            dict: Parsed record.
        """
        
        # Default to internal registry if no layout provided
        if layout is None:
            layout = get_layout

        with open(file_path, 'rb') as f:
            while True:
                record_bytes = f.read(record_length)
                if not record_bytes or len(record_bytes) < record_length:
                    break
                
                # Determine layout
                current_layout = None
                rec_id_str = None
                
                # Peek ID for callable resolution & filtering
                # We assume standard RRC header where first 2 bytes are ID
                try:
                    rec_id_str = codecs.decode(record_bytes[:2], self.encoding)
                except UnicodeDecodeError:
                     rec_id_str = "???"

                if callable(layout):
                    current_layout = layout(rec_id_str)
                else:
                    current_layout = layout
                
                # Handling Inclusion Filtering
                is_included = False
                
                if include:
                    # Explicit inclusion list provided
                    if callable(layout):
                        # For callable layouts (like get_layout), we check if the ID is in the include list
                        # OR if the resulting layout matches one of the include IDs.
                        # But typically 'include' with get_layout means list of Record IDs.
                        if rec_id_str in include:
                            is_included = True
                    else:
                        # Fixed layout mode: include doesn't make much sense unless it matches rec_id?
                        # But normally fixed layout means "parse everything using this layout".
                        # So we might ignore include or check rec_id_str.
                        # Let's assume user wants to filter by ID even with fixed layout if they passed include.
                        if rec_id_str in include:
                            is_included = True
                else:
                    # No explicit include list -> Include everything that has a valid layout
                    if current_layout:
                        is_included = True

                if current_layout and is_included:
                    yield self.parse_record(record_bytes, current_layout, convert_values=convert_values)
                elif not is_included and current_layout:
                     pass # Filtered out
                else:
                    # Unknown record type or no layout found
                    # If include is None (implied "All"), we skip unknown records.
                    pass
