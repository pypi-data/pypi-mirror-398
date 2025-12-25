import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbw3c.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbw3c_parsing(tmp_path):
    # 27 Record
    # 03 1YR 'Y'
    # 18 5YR 'O'
    # 33 10YR 'E'
    # 56 EXT 'F'
    
    f1yr = 'Y'
    f5yr = 'O'
    f10yr = 'E'
    fext = 'F'
    
    line_arr = list(" " * 100) # Length 100
    line_arr[0:2] = list("27")
    line_arr[3-1] = f1yr
    line_arr[18-1] = f5yr
    line_arr[33-1] = f10yr
    line_arr[56-1] = fext
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "".join(line_arr) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser(convert_values=True)
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    rec = wells[0]['WBW3C']
    # Recurring segment -> probably list if multiple, but check if single
    if isinstance(rec, list):
        rec = rec[0]
        
    assert rec['wb_w3c_1yr_flag'] == "1 YEAR REQUIREMENTS MET"
    assert rec['wb_w3c_5yr_flag'] == "OPERATOR OWNS LAND"
    assert rec['wb_w3c_10yr_flag'] == "PART OF EOR PROJECT"
    assert rec['wb_w3c_extension_flag'] == "FALSELY FILED EXCEPTION"
