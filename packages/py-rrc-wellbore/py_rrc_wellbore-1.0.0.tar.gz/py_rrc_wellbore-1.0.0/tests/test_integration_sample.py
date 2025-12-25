import os
import pytest
from py_rrc_wellbore.parser import WellBoreParser

SAMPLE_FILE = "sample.ebc"

def test_integration_sample_ebc():
    """
    Integration test using the real sample.ebc file.
    Verifies that the parser auto-detects EBCDIC and parses the records.
    """
    if not os.path.exists(SAMPLE_FILE):
        pytest.skip(f"{SAMPLE_FILE} not found")

    parser = WellBoreParser(convert_values=True)
    wells = list(parser.parse_file(SAMPLE_FILE))
    
    assert len(wells) > 0, "Should find at least one well"
    
    # Check first well (known from inspection)
    w1 = wells[0]
    assert 'WBROOT' in w1
    
    # API from inspection: 0100100001010106001 -> 133465?
    # Offset 6 length 5: '00100' or similar?
    # Let's just check existence of keys for now
    
    # Check if we parsed children
    children_segments = [k for k in w1 if k != 'WBROOT']
    assert len(children_segments) > 0, "Well 1 should have children (e.g. WBCOMPL)"
    
    # Check basic types
    if 'WBCOMPL' in w1:
        wbcompl = w1['WBCOMPL']
        if isinstance(wbcompl, list):
            assert len(wbcompl) > 0
        else:
            assert isinstance(wbcompl, dict)
            
    # Check for later wells (we saw multiple 01 keys in inspection)
    assert len(wells) > 1, "Should find multiple wells"
