import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wb14b2rm.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wb14b2rm_parsing(tmp_path):
    # 28 Record
    # 3-5 LNE CNT (3)
    # 6-13 DATE (8)
    # 14-21 USERID (8)
    # 22-87 REMARKS (66)
    
    line_arr = list(" " * 100) # Length ~100+ but fixed record likely 144+ based on spec image (starts at 103 for filler)
    # Spec image says record length 144 bytes? No, line 2 is filler PIC X(144). 
    # Wait, POS 103 PIC X(144) filler... that makes record length 247.
    # Standard EBCDIC record length is 247.
    
    line_arr = list(" " * 247)
    line_arr[0:2] = list("28")
    line_arr[3-1:3-1+3] = list("001")
    line_arr[6-1:6-1+8] = list("20230101")
    line_arr[14-1:14-1+8] = list("TESTUSER")
    line_arr[22-1:22-1+66] = list("THIS IS A TEST REMARK FOR 14B2 SEGMENT".ljust(66))
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "".join(line_arr) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    rec = wells[0]['WB14B2RM']
    # Probably list of recurring
    if isinstance(rec, list):
        rec = rec[0]
        
    assert rec['wb_14b2_rmk_lne_cnt'] == 1
    assert rec['wb_14b2_rmk_date'] == 20230101
    assert rec['wb_14b2_rmk_userid'].strip() == "TESTUSER"
    assert rec['wb_14b2_remarks'].strip() == "THIS IS A TEST REMARK FOR 14B2 SEGMENT"
