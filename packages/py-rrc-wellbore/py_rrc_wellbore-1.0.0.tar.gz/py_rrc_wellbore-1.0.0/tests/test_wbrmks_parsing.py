import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbrmks.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbrmks_parsing(tmp_path):
    # 04 Record
    # 03 WB-RMK-LNE-CNT (3) -> 123
    # 06 WB-RMK-TYPE-CODE (1) -> ' '
    # 07 WB-REMARKS (70) -> "THIS IS A REMARK."
    
    remark = "THIS IS A REMARK."
    padded_remark = remark.ljust(70)
    
    line_data = (
        "01" + " " * 100 + "\n" +
        "04" + 
        "123" + 
        " " + 
        padded_remark +
        " " * 100 # Filler
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    rmks = wells[0]['WBRMKS']
    
    assert rmks['wb_rmk_lne_cnt'] == 123
    assert rmks['wb_rmk_type_code'] == ' '
    assert rmks['wb_remarks'].strip() == "THIS IS A REMARK."

def test_wbrmks_multiples(tmp_path):
    line_data = (
        "01" + " " * 100 + "\n" +
        "04" + "001" + " " + "REMARK 1".ljust(70) + "\n" +
        "04" + "002" + " " + "REMARK 2".ljust(70) + "\n"
    )
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    rmks = wells[0]['WBRMKS']
    assert len(rmks) == 2
    assert rmks[0]['wb_remarks'].strip() == "REMARK 1"
    assert rmks[1]['wb_remarks'].strip() == "REMARK 2"
