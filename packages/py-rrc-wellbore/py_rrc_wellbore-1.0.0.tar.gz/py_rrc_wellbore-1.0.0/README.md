# py-rrc-wellbore

A professional-grade Python package for parsing the Texas Railroad Commission (RRC) Well Bore dataset (WBA091).

## Problem Statement

Parsing 1980s-era Texas oil & gas data is a challenge. The data is often delivered in legacy EBCDIC Mainframe format with complex hierarchical structures. This package provides a robust solution to parse this data into modern, usable formats.

## Hierarchical Data Structure

The RRC Well Bore dataset is hierarchical:
- **Record Type '01'**: The Root record (API Number).
- **Subsequent Record Types (02, 03, etc.)**: These records belong to the preceding '01' record until a new '01' record is encountered.

## Installation

```bash
pip install py-rrc-wellbore
```

## Usage

### Basic Usage

Parse a local file (EBCDIC or Text) and iterate through wells:

```python
from py_rrc_wellbore import WellBoreParser

parser = WellBoreParser()

# The parser automatically detects EBCDIC vs ASCII
for well in parser.parse_file("data/wba091.ebc"):
    root = well['WBROOT'] # Key 01
    print(f"API: {root['wb_api_number']}, Lease: {root['wb_lease_name']}")
    
    # Access child segments (e.g., Completions - Key 02)
    if 'WBCOMPL' in well:
        completions = well['WBCOMPL']
        # Child segments can be a list (multiple records) or a dict (single record)
        if isinstance(completions, list):
            for compl in completions:
                print(f"  - Completion Date: {compl.get('wb_compl_date')}")
        else:
             print(f"  - Completion Date: {completions.get('wb_compl_date')}")
```

### Filtering Segments

Optimize performance and output size by requesting only specific segments. You can use segment Keys (e.g., '01', '02') or Names.

```python
# Parse only Root (01) and Casing (06) information
parser = WellBoreParser(segments_to_parse=['ROOT', 'WBCASE'])

for well in parser.parse_file("data/wba091.ebc"):
    # well dictionary will only contain 'WBROOT' and 'WBCASE' keys
    pass
```

### Automatic Value Conversion

The raw data contains many encoded values (e.g., county, district codes). Use `convert_values=True` to automatically map these to human-readable descriptions.

```python
parser = WellBoreParser(convert_values=True)

well = next(parser.parse_file("data/wba091.ebc"))
print(well['WBROOT']['wb_county_code']) 
# Output: 'MIDLAND' (instead of '165')
```

## Sample Data

The repository includes a `sample.ebc` file. This file is a small subset of the full Texas RRC Well Bore database, intended for testing and verification purposes. It contains binary EBCDIC data that the parser is capable of handling correctly.

## Made with Gemini

This library was built with **Gemini Pro 3**, leveraging its advanced agentic capabilities to handle complex EBCDIC parsing and hierarchical data structures with minimal effort.
