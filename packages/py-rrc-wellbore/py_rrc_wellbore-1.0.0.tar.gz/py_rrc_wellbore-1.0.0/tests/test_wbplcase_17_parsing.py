import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbplcase.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbplcase_parsing(tmp_path):
    # 17 Record
    # 03 WB-PLG-CAS-COUNTER (6) -> 000001
    # 09 WB-PLUG-CAS-INCH (2) -> 10
    # 11 WB-PLUG-CAS-FRAC-NUM (2) -> 03
    # 13 WB-PLUG-CAS-FRAC-DENOM (2) -> 04
    # 15 WB-PLUG-WGT-WHOLE (3) -> 040
    # 18 WB-PLUG-WGT-TENTHS (1) -> 5
    # 19 WB-PLUG-AMT-PUT (5) -> 01000
    # 24 WB-PLUG-AMT-LEFT (5) -> 00500
    # 29 WB-PLUG-HOLE-SIZE (2) -> 12
    # 31 WB-PLUG-HOLE-FRAC-NUM (2) -> 01
    # 33 WB-PLUG-HOLE-FRAC-DENOM (2) -> 02
    
    cnt = "000001"
    c_inch = "10"
    c_num = "03"
    c_den = "04"
    w_whole = "040"
    w_tenth = "5"
    amt_put = "01000"
    amt_left = "00500"
    h_inch = "12"
    h_num = "01"
    h_den = "02"
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "17" + 
        cnt + 
        c_inch + c_num + c_den + 
        w_whole + w_tenth + 
        amt_put + 
        amt_left + 
        h_inch + h_num + h_den + 
        (" " * 100) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    plcase = wells[0]['WBPLCASE']
    
    assert plcase['wb_plg_cas_counter'] == 1
    assert plcase['wb_plug_cas_inch'] == 10
    assert plcase['wb_plug_cas_frac_num'] == 3
    assert plcase['wb_plug_cas_frac_denom'] == 4
    assert plcase['wb_plug_wgt_whole'] == 40
    assert plcase['wb_plug_wgt_tenths'] == 5
    assert plcase['wb_plug_amt_put'] == 1000
    assert plcase['wb_plug_amt_left'] == 500
    assert plcase['wb_plug_hole_inch'] == 12
    assert plcase['wb_plug_hole_frac_num'] == 1
    assert plcase['wb_plug_hole_frac_denom'] == 2
