import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbplrec.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbplrec_parsing(tmp_path):
    # 16 Record
    # 03 WB-PLUG-NUMBER (3) -> 001
    # 06 WB-NBR-OF-CEMENT-SACKS (5) -> 00050
    # 11 WB-MEAS-TOP-OF-PLUG (5) -> 05000
    # 16 WB-BOTTOM-TUBE-PIPE-DEPTH (5) -> 05100
    # 21 WB-PLUG-CALC-TOP (5) -> 04950
    # 26 WB-PLUG-TYPE-CEMENT (6) -> "CLASS A"
    
    p_num = "001"
    sacks = "00050"
    meas_top = "05000"
    bott_tube = "05100"
    calc_top = "04950"
    c_type = "CLASSC" # 6 chars
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "16" + 
        p_num + 
        sacks + 
        meas_top + 
        bott_tube + 
        calc_top + 
        c_type + 
        (" " * 100) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    plrec = wells[0]['WBPLREC']
    
    assert plrec['wb_plug_number'] == 1
    assert plrec['wb_nbr_of_cement_sacks'] == 50
    assert plrec['wb_meas_top_of_plug'] == 5000
    assert plrec['wb_plug_type_cement'] == "CLASSC"
