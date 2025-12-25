import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbdate.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbdate_parsing(tmp_path):
    # 03 Record
    # 03 WB-FILE-KEY (8) -> 87654321
    # 11 WB-FILE-DATE (8) -> 20230101
    
    line_data = (
        "01" + " " * 100 + "\n" +
        "03" + 
        "87654321" + 
        "20230101" +
        " " * 100
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    date_rec = wells[0]['WBDATE']
    
    assert date_rec['wb_file_key'] == 87654321
    assert date_rec['wb_file_date'] == 20230101

def test_wbdate_lookups(tmp_path):
    # Test lookup conversion
    # 90 WB-ELEVATION-CODE (2) -> 'GL'
    
    # Construct line padded to 90
    # 02 (Key) + 88 filler = 90 start (1-based pos 90 matches index 89, so 2+87 chars?)
    # Layout 03: 90, 2 is elevation code.
    # Key is 2 chars. 89-2 = 87 chars padding.
    
    line_data = (
        "01" + " " * 100 + "\n" +
        "03" + " " * 87 + "GL" + " " * 100
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser(convert_values=True)
    wells = list(parser.parse_file(fpath))
    
    date_rec = wells[0]['WBDATE']
    assert date_rec['wb_elevation_code'] == 'GROUND LEVEL'
