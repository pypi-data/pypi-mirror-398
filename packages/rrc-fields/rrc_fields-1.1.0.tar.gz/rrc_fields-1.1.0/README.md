# rrc-fields

A comprehensive Python parser for Texas Railroad Commission (RRC) field data in EBCDIC format.

This library parses the raw EBCDIC tape files from the Texas Railroad Commission's Oil & Gas Division, converting them into structured, human-readable JSON. It supports 30 distinct record segments, handling complex COBOL data types like signed zoned decimals, packed decimals (COMP-3), and implied decimal scaling.

> **Note**: This project was created completely with minimal effort and Gemini 3 Pro.

## Installation

```bash
pip install rrc-fields
```

## Usage Examples

### 1. Basic Usage (Simple Parsing)

The simplest way to use `rrc-fields` is to parse a file and get the raw records.

```python
from rrc_fields import RRCFieldParser
import json

parser = RRCFieldParser()
# Parse the tape file
# Returns a generator or list of dictionaries
records = parser.parse_file('path/to/field_tape.ebc')

for record in records:
    print(record)
```

### 2. Advanced Usage (Value Conversion & Filtering)

You can enable value conversion to get human-readable labels instead of raw codes, and filter by record type to process only specific data segments (e.g., just the Field Root records).

```python
from rrc_fields import RRCFieldParser

parser = RRCFieldParser()

# 'convert_values=True': Converts codes like 'G' to 'GAS FIELD'
# 'include': Only return records with these IDs
# Note: layout is optional and defaults to loading all known segments
records = parser.parse_file(
    'path/to/field_tape.ebc', 
    convert_values=True,
    include=['01']  # Only get Field Root (01) records
)

for record in records:
    print(f"Field: {record.get('FL_FIELD_NAME')} ({record.get('FL_FIELD_TYPE')})")
```

### 3. Complex Example: Generating a Hierarchical JSON

In many cases, you want to group related records (like Gas Info segments) under their parent Field record. Here is how you might structure the data.

```python
from rrc_fields import RRCFieldParser
import json

def process_tape_to_hierarchy(file_path):
    parser = RRCFieldParser()
    all_records = parser.parse_file(file_path, convert_values=True)
    
    fields = {}
    current_field_id = None
    
    for rec in all_records:
        rec_id = rec.get('RRC_TAPE_RECORD_ID')
        
        # Record 01 is the Field Root
        if rec_id == '01':
            field_no = rec.get('FL_FIELD_NUMBER')
            current_field_id = field_no
            fields[field_no] = {
                'info': rec,
                'gas_segments': [],
                'oil_segments': [],
                'remarks': []
            }
            
        # Other records belong to the current field
        elif current_field_id:
            if rec_id == '02': # Gas Segment
                fields[current_field_id]['gas_segments'].append(rec)
            elif rec_id == '19': # Oil Segment
                fields[current_field_id]['oil_segments'].append(rec)
            elif rec_id in ['05', '06', '10']: # Remarks
                fields[current_field_id]['remarks'].append(rec)

    return fields

# Run the processing
hierarchy = process_tape_to_hierarchy('field_tape.ebc')

# Save to file
with open('fields_hierarchy.json', 'w') as f:
    json.dump(hierarchy, f, indent=2)
```

## Output Format

The parser returns a flat list of dictionaries by default. Below is an expanded example of what a parsed record looks like.

### Example Output (JSON)

```json
[
  {
    "RRC_TAPE_RECORD_ID": "01",
    "FL_FIELD_DISTRICT": "01",
    "FL_FIELD_NUMBER": 123456,
    "FL_FIELD_NAME": "EXAMPLE FIELD",
    "FL_FIELD_TYPE": "GAS FIELD",
    "FL_FIELD_CLASS": "GAS",
    "FL_RAILROAD_COMM_DISTRICT": "01",
    "FL_FIELD_RULE_TYPE": "REGULAR"
  },
  {
    "RRC_TAPE_RECORD_ID": "02",
    "FL_GAS_DISC_COUNTY_CODE": "123",
    "FL_GAS_DISCOVERY_DATE": "19950101",
    "FL_GAS_AVG_GRAVITY": 0.65,
    "FL_GAS_AVG_BTU": 1050,
    "FL_GAS_ALLOCATION_FORMULA": "100% ACREAGE",
    "FL_GAS_WELL_COUNT": 5
  }
]
```

## Supported Record Segments

This parser supports all 30 documented field tape record usage types:

| ID | Segment Name | Description |
|:---|:-------------|:------------|
| 01 | `FLDROOT` | Field Root Information (District, Field Name, Type) |
| 02 | `GASSEG` | Gas Field Information |
| 03 | `FLMKTDMD` | Field Market Demand Forecast |
| 04 | `OPRMKTDM` | Operator Market Demand Forecast |
| 05 | `FLMKTRMK` | Field Market Demand Remarks |
| 06 | `FLSUPRMK` | Field Market Demand Supplement Remarks |
| 07 | `GASCYCLE` | Field Gas Cycle Information |
| 08 | `GSFLDRUL` | Field Gas Rules (Spacing, allocation) |
| 09 | `GASAFORM` | Field Gas Allocation Formula |
| 10 | `GASRMRKS` | Field Gas Remarks |
| 11 | `GSCOUNTY` | Field Gas County Codes |
| 12 | `GASAFACT` | Field Gas Allocation Factors |
| 13 | `ASHEET` | Allowable Sheet Root |
| 14 | `ASHEETMO` | Allowable Sheet Monthly Information |
| 15 | `FLT3ROOT` | Field T-3 Form Root |
| 16 | `FLDT3` | Field T-3 Form Data |
| 17 | `FLDMO` | Field Monthly Stats |
| 18 | `CALC49B` | 49(b) Calculation Information |
| 19 | `OILSEG` | Oil Field Information |
| 20 | `OILCYCLE` | Oil Cycle Information |
| 21 | `OLFLDRUL` | Oil Field Rules |
| 22 | `OILAFORM` | Oil Allocation Formula |
| 23 | `OILRMRKS` | Oil Remarks |
| 24 | `OILFTROT` | Oil Factors Root |
| 25 | `OILAFACT` | Oil Allocation Factors |
| 26 | `OLCOUNTY` | Oil Field County |
| 27 | `ASSOCGAS` | Associated Gas Fields |
| 28 | `FLDMAP` | Field Map Index |
| 29 | `GSOPTRUL` | Gas Optional Rules |
| 30 | `OLOPTRUL` | Oil Optional Rules |


## Getting sample ebc from large.ebc

```bash
dd if=main.ebc of=sample.ebc bs=1024 count=100
```