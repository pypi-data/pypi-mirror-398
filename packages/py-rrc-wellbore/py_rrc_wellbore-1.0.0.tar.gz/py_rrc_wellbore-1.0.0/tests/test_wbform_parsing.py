import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbform.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbform_parsing(tmp_path):
    # 09 Record
    # 03 WB-FORMATION-CNTR (3) -> 001
    # 06 WB-FORMATION-NAME (32) -> "AUSTIN CHALK"
    # 38 WB-FORMATION-DEPTH (5) -> 09000
    
    name = "AUSTIN CHALK"
    padded_name = name.ljust(32)
    
    line_data = (
        "01" + " " * 100 + "\n" +
        "09" + 
        "001" + 
        padded_name +
        "09000" +
        " " * 100
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    form = wells[0]['WBFORM']
    
    assert form['wb_formation_cntr'] == 1
    assert form['wb_formation_name'].strip() == "AUSTIN CHALK"
    assert form['wb_formation_depth'] == 9000
