import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbline.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbline_parsing(tmp_path):
    # 08 Record
    # 03 WB-LINE-COUNT (3) -> 1
    # 06 WB-LIN-INCH (2) -> 05
    # 08 WB-LIN-FRAC-NUM (2) -> 01
    # 10 WB-LIN-FRAC-DENOM (2) -> 02
    # 12 WB-SACKS-OF-CEMENT (5) -> 00100
    # 17 WB-TOP-OF-LINER (5) -> 05000
    # 22 WB-BOTTOM-OF-LINER (5) -> 06000
    
    line_data = (
        "01" + " " * 100 + "\n" +
        "08" + 
        "001" + 
        "05" + 
        "01" + 
        "02" + 
        "00100" +
        "05000" +
        "06000" +
        " " * 100
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    liner = wells[0]['WBLINE']
    
    assert liner['wb_line_count'] == 1
    assert liner['wb_lin_inch'] == 5
    assert liner['wb_lin_frac_num'] == 1
    assert liner['wb_lin_frac_denom'] == 2
    assert liner['wb_sacks_of_cement'] == 100
    assert liner['wb_top_of_liner'] == 5000
    assert liner['wb_bottom_of_liner'] == 6000
