import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbsqeze.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbsqeze_parsing(tmp_path):
    # 10 Record
    # 03 WB-SQUEEZE-CNTR (3) -> 001
    # 06 WB-SQUEEZE-UPPER-DEPTH (5) -> 08000
    # 11 WB-SQUEEZE-LOWER-DEPTH (5) -> 08100
    # 16 WB-SQUEEZE-KIND-AMOUNT (50) -> "CEMENT SQUEEZE"
    
    kind = "CEMENT SQUEEZE"
    padded_kind = kind.ljust(50)
    
    line_data = (
        "01" + " " * 100 + "\n" +
        "10" + 
        "001" + 
        "08000" +
        "08100" +
        padded_kind +
        " " * 100
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    sq = wells[0]['WBSQEZE']
    
    assert sq['wb_squeeze_cntr'] == 1
    assert sq['wb_squeeze_upper_depth'] == 8000
    assert sq['wb_squeeze_lower_depth'] == 8100
    assert sq['wb_squeeze_kind_amount'].strip() == "CEMENT SQUEEZE"
