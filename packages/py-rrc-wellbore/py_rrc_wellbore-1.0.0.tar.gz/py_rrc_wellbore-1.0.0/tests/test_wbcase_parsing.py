import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbcase.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbcase_parsing(tmp_path):
    # 06 Record
    # 03 WB-CASING-COUNT (3) -> 001
    # 06 WB-CAS-INCH (2) -> 07
    # 08 WB-CAS-FRAC-NUM (2) -> 00
    # 10 WB-CAS-FRAC-DENOM (2) -> 00
    # 12 WB-WGT-WHOLE-1 (3) -> 020
    # 15 WB-WGT-TENTHS-1 (1) -> 0
    # 16 WB-WGT-WHOLE-2 (3) -> 000
    # 19 WB-WGT-TENTHS-2 (1) -> 0
    # 20 WB-CASING-DEPTH-SET (5) -> 03000
    # 25 WB-MLTI-STG-TOOL-DPTH (5) -> 00000
    # 30 WB-AMOUNT-OF-CEMENT (5) -> 00500
    # 35 WB-CEMENT-MEASUREMENT (1) -> 'S'
    # 36 WB-HOLE-INCH (2) -> 09
    # 38 WB-HOLE-FRAC-NUM (2) -> 07
    # 40 WB-HOLE-FRAC-DENOM (2) -> 08
    # 42 FILLER -> ' '
    # 43 WB-TOP-OF-CEMENT-CASING (7) -> '000100 '
    # 50 WB-AMOUNT-CASING-LEFT (5) -> 00000
    
    line_data = (
        "01" + " " * 100 + "\n" +
        "06" + 
        "001" + 
        "07" + 
        "00" + 
        "00" + 
        "020" + "0" + 
        "000" + "0" +
        "03000" +
        "00000" +
        "00500" +
        "S" +
        "09" +
        "07" +
        "08" +
        " " + 
        "000100 " +
        "00000" +
        " " * 100
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser(convert_values=True)
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    case = wells[0]['WBCASE']
    
    assert case['wb_casing_count'] == 1
    assert case['wb_cas_inch'] == 7
    assert case['wb_wgt_whole_1'] == 20
    assert case['wb_casing_depth_set'] == 3000
    assert case['wb_amount_of_cement'] == 500
    assert case['wb_cement_measurement'] == 'SACKS'
    assert case['wb_hole_inch'] == 9
    assert case['wb_top_of_cement_casing'].strip() == '000100'

def test_wbcase_lookups(tmp_path):
    # Test just usage of cement measurement lookup
    # 35 -> 'Y'
    line_data = (
        "01" + " " * 100 + "\n" +
        "06" + " " * 32 + "Y" + " " * 100
    )
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser(convert_values=True)
    wells = list(parser.parse_file(fpath))
    
    assert wells[0]['WBCASE']['wb_cement_measurement'] == 'CUBIC YARDS'
