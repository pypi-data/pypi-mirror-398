import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbtube.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbtube_parsing(tmp_path):
    # 05 Record
    # 03 WB-SEGMENT-COUNTER (3) -> 001
    # 06 WB-TUBING-INCHES (2) -> 05
    # 08 WB-FR-NUMERATOR (2) -> 01
    # 10 WB-FR-DENOMINATOR (2) -> 02 (5 1/2 inches)
    # 12 WB-DEPTH-SET (5) -> 05000
    # 17 WB-PACKER-SET (5) -> 04950
    
    line_data = (
        "01" + " " * 100 + "\n" +
        "05" + 
        "001" + 
        "05" + 
        "01" + 
        "02" + 
        "05000" +
        "04950" +
        " " * 100
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    tube = wells[0]['WBTUBE']
    
    assert tube['wb_segment_counter'] == 1
    assert tube['wb_tubing_inches'] == 5
    assert tube['wb_fr_numerator'] == 1
    assert tube['wb_fr_denominator'] == 2
    assert tube['wb_depth_set'] == 5000
    assert tube['wb_packer_set'] == 4950
