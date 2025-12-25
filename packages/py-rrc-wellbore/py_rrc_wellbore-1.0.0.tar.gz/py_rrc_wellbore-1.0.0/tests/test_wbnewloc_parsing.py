import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbnewloc.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbnewloc_parsing(tmp_path):
    # 13 Record
    # 03 WB-LOC-COUNTY (3) -> 101
    # 06 WB-ABSTRACT (6) -> "A-123 "
    # 12 WB-SURVEY (55) -> "TEST SURVEY"
    # 178 WB-VERIFICATION-FLAG (1) -> "Y" -> "VERIFIED"
    
    county = "101"
    abstract = "A-123".ljust(6)
    survey = "TEST SURVEY".ljust(55)
    flag = "Y"
    
    # Needs full padding.
    # Pos 1-2: 13
    # Pos 3-5: 101
    # Pos 6-11: Abstract
    # Pos 12-66: Survey
    # ...
    # Pos 178: Flag
    # Total length > 178
    

    
    line_data = (
        "01" + " " * 200 + "\n" +
        "13" + 
        county + 
        abstract + 
        survey + 
        (" " * 111) + 
        flag + 
        (" " * 50) # Trailing
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    # Test Raw
    parser = WellBoreParser(convert_values=False)
    wells = list(parser.parse_file(fpath))
    newloc = wells[0]['WBNEWLOC']
    assert newloc['wb_loc_county'] == 101
    assert newloc['wb_abstract'].strip() == "A-123"
    assert newloc['wb_verification_flag'] == "Y"
    
    # Test Conversion
    parser_conv = WellBoreParser(convert_values=True)
    wells_conv = list(parser_conv.parse_file(fpath))
    newloc_conv = wells_conv[0]['WBNEWLOC']
    assert newloc_conv['wb_verification_flag'] == "VERIFIED"
