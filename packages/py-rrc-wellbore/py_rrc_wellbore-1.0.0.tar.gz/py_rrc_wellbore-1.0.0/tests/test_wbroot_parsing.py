import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbroot.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbroot_parsing_extraction(tmp_path):
    # Construct a line based on spec
    # 01 (2) + 003 (3) + 12345 (5) ...
    # Let's build it rigorously or just pad nicely.
    # 01 + 003 + 12345 + 00 + 00 + 00 + ...
    
    # Using specific values to verify extraction
    # Pos 1: 01
    # Pos 3: 003 (County) -> 003
    # Pos 6: 12345 (Unique) -> 12345
    # Pos 11: 99 (Suffix) -> 99
    # Pos 20: 1 (Cent Flag) -> '1' (19th)
    # Pos 55: A (Denial Flag) -> 'A'
    

    # Adjust line to match specific fields tested
    # 01 (1-2)
    # 003 (3-5) -> api_county_code
    # 12345 (6-10) -> api_unique_number
    # 99 (11-12) -> next_avail_suffix
    # 88 (13-14) -> next_avail_hole_chge_nbr
    # 77 (15-16) -> field_district
    # 666 (17-19) -> res_cnty_code
    # 1 (20) -> orig_compl_cc_flag
    
    line_data = "01003123459988776661" + " " * 200

    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))

    
    assert len(wells) == 1
    root = wells[0]['WBROOT']
    
    assert root['api_county_code'] == 3
    assert root['api_unique_number'] == 12345
    assert root['next_avail_suffix'] == 99
    assert root['next_avail_hole_chge_nbr'] == 88
    assert root['field_district'] == 77
    assert root['res_cnty_code'] == 666
    assert root['orig_compl_cc_flag'] == '1'

def test_wbroot_value_conversion(tmp_path):
    # Test lookups
    # Pos 20: 1 (19TH CENTURY)
    # Pos 55: A (AUTOMATIC)
    # Pos 55 is denial_reason_flag
    
    # Need to find pos 55 offset.
    # 1-20 is known length 20.
    # 21-22: cent
    # 23-24: yy
    # 25-26: mm
    # 27-28: dd
    # 29-33: depth (5)
    # 34-38: fluid (5)
    # 39-40: rev cc
    # 41-42: rev yy
    # 43-44: rev mm
    # 45-46: rev dd
    # 47-48: den cc
    # 49-50: den yy
    # 51-52: den mm
    # 53-54: den dd
    # 55: flag (1)
    
    # Prefix length to 55: 54 chars.
    
    prefix = "01" + "0"*52 
    # Current len: 2 + 52 = 54. 
    # Next char is at 55.
    
    # We want Pos 20 to be '1'.
    # 0-based idx 19.
    # original prefix: '01' (0,1). '0'*52 fills 2..53.
    # Modify char at 19.
    
    line_list = list(prefix + "A" + " " * 100) # 55 is 'A'
    line_list[19] = '1' # Pos 20 is '1'
    
    line_data = "".join(line_list)
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser(convert_values=True)
    wells = list(parser.parse_file(fpath))
    
    root = wells[0]['WBROOT']
    
    assert root['orig_compl_cc_flag'] == '19TH CENTURY'
    assert root['denial_reason_flag'] == 'AUTOMATIC'

