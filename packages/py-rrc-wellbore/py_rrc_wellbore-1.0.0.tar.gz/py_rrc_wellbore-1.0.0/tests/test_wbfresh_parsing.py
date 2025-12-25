import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbfresh.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbfresh_parsing(tmp_path):
    # 11 Record
    # 03 WB-FRESH-WATER-CNTR (3) -> 001
    # 06 WB-TWDB-DATE (8) -> 20230101
    # 14 WB-SURFACE-CASING-DETER-CODE (1) -> "Y"
    # 15 WB-UQWP-FROM (4) -> 0100
    # 19 WB-UQWP-TO (4) -> 0200
    
    line_data = (
        "01" + " " * 100 + "\n" +
        "11" + 
        "001" + 
        "20230101" +
        "Y" + 
        "0100" +
        "0200" +
        " " * 100
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    fresh = wells[0]['WBFRESH']
    
    assert fresh['wb_fresh_water_cntr'] == 1
    assert fresh['wb_twdb_date'] == 20230101
    assert fresh['wb_surface_casing_deter_code'] == "Y"
    assert fresh['wb_uqwp_from'] == 100
    assert fresh['wb_uqwp_to'] == 200
