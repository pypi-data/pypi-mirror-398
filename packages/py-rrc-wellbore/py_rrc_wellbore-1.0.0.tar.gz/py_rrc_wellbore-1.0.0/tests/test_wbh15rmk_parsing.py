import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbh15rmk.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbh15rmk_parsing(tmp_path):
    # 24 Record
    # 03 KEY (3) -> 001
    # 06 TEXT (70) -> "THIS IS A TEST REMARK FOR H15 SEGMENT"
    
    key = "001"
    text = "THIS IS A TEST REMARK FOR H15 SEGMENT".ljust(70)
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "24" + 
        key + 
        text + 
        (" " * 10) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    rmk = wells[0]['WBH15RMK']
    # Remarks are typically recurring, likely returned as a list if the parser enforces it or if multiple exist.
    # If single line, it might be dict or list depending on implementation.
    # Let's assume dict for single.
    
    assert rmk['wb_h15_remark_key'] == 1
    assert rmk['wb_h15_remark_text'].strip() == "THIS IS A TEST REMARK FOR H15 SEGMENT"

def test_wbh15rmk_multiple(tmp_path):
    line1 = "24001REMARK ONE" + (" " * 60)
    line2 = "24002REMARK TWO" + (" " * 60)
    
    data = (
        "01" + " " * 200 + "\n" +
        line1 + "\n" +
        line2 + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    rmks = wells[0]['WBH15RMK']
    assert isinstance(rmks, list)
    assert len(rmks) == 2
    assert rmks[0]['wb_h15_remark_text'].strip() == "REMARK ONE"
    assert rmks[1]['wb_h15_remark_text'].strip() == "REMARK TWO"
