import pytest
from py_rrc_wellbore.parser import WellBoreParser
from unittest.mock import MagicMock

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_hierarchical_grouping(tmp_path):
    content = (
        "01 Root1\n"
        "02 Child1A\n"
        "03 Date1\n"
        "01 Root2\n"
        "02 Child2A\n"
        "02 Child2B\n"
    )
    fpath = create_dummy_file(tmp_path, content)
    
    # Patch LAYOUTS to empty so parser falls back to raw_record
    from unittest.mock import patch
    with patch('py_rrc_wellbore.parser.LAYOUTS', {}):
        parser = WellBoreParser()
        wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 2
    

    # Check Well 1
    w1 = wells[0]
    assert 'WBROOT' in w1
    assert 'WBCOMPL' in w1
    assert 'WBDATE' in w1
    assert isinstance(w1['WBCOMPL'], dict) # Single child
    assert w1['WBROOT']['raw_record'] == "01 Root1"
    
    # Check Well 2
    w2 = wells[1]
    assert 'WBROOT' in w2
    assert 'WBCOMPL' in w2
    assert isinstance(w2['WBCOMPL'], list) # Multiple children
    assert len(w2['WBCOMPL']) == 2
    assert w2['WBCOMPL'][0]['raw_record'] == "02 Child2A"
    assert w2['WBCOMPL'][1]['raw_record'] == "02 Child2B"

def test_segment_filtering(tmp_path):
    content = (
        "01 Root1\n"
        "02 Child1A\n"
        "03 Date1\n"
    )
    fpath = create_dummy_file(tmp_path, content)
    
    # Filter only WBROOT ('01') and WBDATE ('03'), exclude WBCOMPL ('02')
    # Providing mix of codes and names
    parser = WellBoreParser(segments_to_parse=['01', 'WBROOT', '03']) 
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    w1 = wells[0]
    assert 'WBROOT' in w1
    assert 'WBDATE' in w1
    assert 'WBCOMPL' not in w1

def test_value_conversion_mock(tmp_path):
    content = "01 Root1\n"
    fpath = create_dummy_file(tmp_path, content)
    
    parser = WellBoreParser(convert_values=True)
    
    # Mock _extract_data to return a dict with a code
    original_extract = parser._extract_data
    
    def mock_extract(key, line):
        data = original_extract(key, line)
        if key == '01':
            data['county_code'] = '003' # Should convert to ANDREWS
        return data
        
    parser._extract_data = mock_extract
    
    wells = list(parser.parse_file(fpath))
    w1 = wells[0]
    
    # Needs to match what's in Lookups for WBROOT now
    # We never populated 'county_code' in LOOKUPS real structure fully, but mock test assumed it.
    # But wait, mappings.py has LOOKUPS. If we use real Parser, it uses real LOOKUPS.
    # The real LOOKUPS for WBROOT doesn't have 'county_code' yet in my update (I removed the placeholders).
    # I should update this test to use a field that EXISTS in real LOOKUPS, e.g., 'denial_reason_flag'.
    
    # ACTUALLY, I shouldn't try to be too clever in a mock test.
    # But wait, the test patches _extract_data but uses real _apply_conversions -> real LOOKUPS.
    # Real LOOKUPS['WBROOT'] has keys like 'denial_reason_flag'.
    # Let's use 'denial_reason_flag' = 'A'.
    
    # Re-writing the test logic slightly to be robust with new mappings
    pass

def test_value_conversion_real(tmp_path):
    # Testing with a real field from mappings
    content = "01 Root1\n"
    fpath = create_dummy_file(tmp_path, content)
    parser = WellBoreParser(convert_values=True)
    
    original_extract = parser._extract_data
    def mock_extract(key, line):
        data = original_extract(key, line)
        if key == '01':
            data['denial_reason_flag'] = 'A'
        return data
    parser._extract_data = mock_extract
    
    wells = list(parser.parse_file(fpath))
    w1 = wells[0]
    assert w1['WBROOT']['denial_reason_flag'] == 'AUTOMATIC'
