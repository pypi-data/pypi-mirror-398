import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbdrill.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbdrill_parsing(tmp_path):
    # 20 Record
    # 03 WB-PERMIT-NUMBER (6) -> 123456
    
    permit_num = "123456"
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "20" + 
        permit_num + 
        (" " * 50) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    drill = wells[0]['WBDRILL']
    
    # Check if recurring/list or single/dict.
    # WBDRILL is usually marked RECURRING in spec if multiple permits exist.
    # But for single line, it will be a dict unless we have multiple lines.
    # Let's assume it works like others: single -> dict.
    
    assert drill['wb_permit_number'] == 123456

def test_wbdrill_multiple(tmp_path):
    # Test recurring behavior
    line1 = "20123456" + " " * 50
    line2 = "20654321" + " " * 50
    
    data = (
        "01" + " " * 200 + "\n" +
        line1 + "\n" +
        line2 + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    drill = wells[0]['WBDRILL']
    assert isinstance(drill, list)
    assert len(drill) == 2
    assert drill[0]['wb_permit_number'] == 123456
    assert drill[1]['wb_permit_number'] == 654321
