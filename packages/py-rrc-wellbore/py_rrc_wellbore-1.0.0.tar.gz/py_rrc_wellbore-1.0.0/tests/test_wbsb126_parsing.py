import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbsb126.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbsb126_parsing(tmp_path):
    # 25 Record
    # 03 DESIG FLAG 'A' (AUTOMATICALLY DESIGNATED)
    # ...
    # 46 DENIAL FLAG 'M' (MANUALLY DENIED)
    
    desig = 'A'
    denial = 'M'
    
    # 1-2 '25'
    # 3 Desig (1)
    # 4-9 Eff Date (6)
    # 10-15 Rev Date (6)
    # 16-23 Let Date (8)
    # 24-29 Cert Eff (6)
    # 30-37 Revoked (8)
    # 38-45 Denial (8)
    # 46 Denial Flag (1)
    
    # Construct line
    line_arr = list(" " * 60) # Record length 60
    line_arr[0:2] = list("25")
    line_arr[3-1] = desig
    line_arr[46-1] = denial
    
    # Dates 0s
    line_arr[4-1:4-1+6] = list("000000")
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "".join(line_arr) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser(convert_values=True)
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    rec = wells[0]['WBSB126']
    
    assert rec['wb_sb126_designation_flag'] == "AUTOMATICALLY DESIGNATED"
    assert rec['wb_sb126_denial_reason_flag'] == "MANUALLY DENIED"
    assert rec['wb_sb126_desig_effective_date'] == 0
