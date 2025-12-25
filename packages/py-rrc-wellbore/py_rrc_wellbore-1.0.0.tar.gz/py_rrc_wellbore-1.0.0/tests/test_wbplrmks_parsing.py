import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbplrmks.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbplrmks_parsing(tmp_path):
    # 15 Record
    # 03 WB-PLUG-RMK-LNE-CNT (3) -> 001
    # 06 WB-PLUG-RMK-TYPE-CODE (1) -> " " (Not used)
    # 07 WB-PLUG-REMARKS (70) -> "THIS IS A TEST PLUGGING REMARK"
    
    cnt = "001"
    type_code = " "
    remarks = "THIS IS A TEST PLUGGING REMARK".ljust(70)
    
    # Needs padding to 77 minimum (start 7 + 70 = 76 end).
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "15" + 
        cnt + 
        type_code + 
        remarks + 
        (" " * 50) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    plrmks = wells[0]['WBPLRMKS']
    # Should be list since it's recurring?
    # Wait, Parser logic: if key exists, it converts to list.
    # But here we only have one line. So it might be a dict. 
    # Let's check if my parser handles explicit 'recurring' flag? 
    # No, currently it just appends if key exists.
    # So for single occurrence, it's a dict.
    
    assert plrmks['wb_plug_rmk_lne_cnt'] == 1
    assert plrmks['wb_plug_rmk_type_code'].strip() == "" # Strip default
    assert plrmks['wb_plug_remarks'].strip() == "THIS IS A TEST PLUGGING REMARK"

def test_wbplrmks_multiple(tmp_path):
    # Test multiple remarks to ensure list handling
    line1 = "15001 THIS IS REMARK 1".ljust(80)
    line2 = "15002 THIS IS REMARK 2".ljust(80)
    
    # 15 (2) + 001 (3) + " " (1) + "THIS..." (70)
    # Actually my simple concat above:
    # "15" + "001" + " " + "THIS..."
    
    l1 = (
        "15" + 
        "001" + 
        " " + 
        "THIS IS REMARK 1".ljust(70)
    )
    l2 = (
        "15" + 
        "002" + 
        " " + 
        "THIS IS REMARK 2".ljust(70)
    )
    
    data = (
        "01" + " " * 200 + "\n" +
        l1 + "\n" + 
        l2 + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    plrmks = wells[0]['WBPLRMKS']
    assert isinstance(plrmks, list)
    assert len(plrmks) == 2
    assert plrmks[0]['wb_plug_rmk_lne_cnt'] == 1
    assert plrmks[1]['wb_plug_rmk_lne_cnt'] == 2
