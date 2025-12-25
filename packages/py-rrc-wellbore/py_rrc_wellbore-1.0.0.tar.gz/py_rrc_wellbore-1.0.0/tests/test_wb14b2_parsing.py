import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wb14b2.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wb14b2_parsing(tmp_path):
    # 22 Record
    # 03 WB14B2-OIL-CODE 'O' (1)
    # ...
    # 25 STATUS 'A' (APPROVED)
    # 26 REASON 'T' (INJECTION WELL)
    # 59 MECH-INTEG 'H'
    
    oil_code = "O"
    status = "A"
    reason = "T"
    mech_viol = "H"
    
    # Pad to 59 (start of mech viol is 59)
    # 01-02 ID
    # 03-58 Data (56 chars)
    # 59 Mech Viol
    
    # Let's build it carefully
    # 1-2: "22"
    # 3: 'O'
    # 4-5: "08" (Dist)
    # 6-10: "00123" (Lease)
    # 11-16: "000001" (Well)
    # 17-22: "000000" (App)
    # 23-24: "00" (Gas Dist)
    # 25: 'A'
    # 26: 'T'
    # 27-58: Zeros/Spaces. Let's assume Zeros for dates (8*4=32 chars).
    # 27+32 = 59. Correct. 
    
    dates = "0" * 32
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "22" + 
        oil_code + 
        "08" + 
        "00123" + 
        "000001" + 
        "000000" + 
        "00" + 
        status + 
        reason + 
        dates + 
        mech_viol + 
        (" " * 100) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    # Test Conversion
    parser = WellBoreParser(convert_values=True)
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    rec = wells[0]['WB14B2']
    
    assert rec['wb14b2_oil_code'] == "O"
    assert rec['wb14b2_ext_status_flag'] == "APPROVED"
    assert rec['wb14b2_ext_cancelled_reason'] == "INJECTION WELL"
    assert rec['wb14b2_mech_integ_viol_flag'] == "MECHANICAL INTEGRITY VIOLATION"
    
    # Test Raw
    parser_raw = WellBoreParser(convert_values=False)
    wells_raw = list(parser_raw.parse_file(fpath))
    rec_raw = wells_raw[0]['WB14B2']
    
    assert rec_raw['wb14b2_ext_status_flag'] == "A"
    assert rec_raw['wb14b2_mech_integ_viol_flag'] == "H"
