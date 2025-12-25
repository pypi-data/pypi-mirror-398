import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbperf.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbperf_parsing(tmp_path):
    # 07 Record
    # 03 WB-PERF-COUNT (3) -> 1
    # 06 WB-FROM-PERF (5) -> 10000
    # 11 WB-TO-PERF (5) -> 11000
    # 16 WB-OPEN-HOLE-CODE (2) -> 'OH'
    
    line_data = (
        "01" + " " * 100 + "\n" +
        "07" + 
        "001" + 
        "10000" + 
        "11000" +
        "OH" +
        " " * 100
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser(convert_values=True)
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    perf = wells[0]['WBPERF']
    
    assert perf['wb_perf_count'] == 1
    assert perf['wb_from_perf'] == 10000
    assert perf['wb_to_perf'] == 11000
    assert perf['wb_open_hole_code'] == 'OPEN HOLE'
