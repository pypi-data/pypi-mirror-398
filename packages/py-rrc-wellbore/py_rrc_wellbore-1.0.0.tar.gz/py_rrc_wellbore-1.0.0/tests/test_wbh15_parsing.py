import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbh15.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbh15_parsing(tmp_path):
    # 23 Record
    # 11 STATUS 'C' (COMPLIANT)
    # 44 O/G Code 'G' (GAS WELL)
    # 76 TYPE TEST 'M' (MECH INTEG)
    # 83 FLUID ' '
    # 84 MECH INTEG 'H' (HYDRAULIC)
    
    status = 'C'
    og = 'G'
    type_test = 'M'
    mech_integ = 'H'
    
    # Needs to be padded correctly
    # 1-2 '23'
    # 3-10 Data (8)
    # 11 Status (1)
    # ...
    # 44 O/G (1)
    # ...
    # 76 Type Test (1)
    # ...
    # 84 Mech Integ (1)
    
    # Let's construct a minimal valid line (others spaces/zeros)
    line_arr = list(" " * 200)
    line_arr[0:2] = list("23")
    
    # 1-based index in spec -> 0-based in python list: index = pos - 1
    line_arr[11-1] = status
    line_arr[44-1] = og
    line_arr[76-1] = type_test
    line_arr[84-1] = mech_integ
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "".join(line_arr) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    # Test Conversion
    parser = WellBoreParser(convert_values=True)
    wells = list(parser.parse_file(fpath))
    assert len(wells) == 1
    rec = wells[0]['WBH15']
    
    assert rec['wb_h15_status'] == "COMPLIANT"
    assert rec['wb_h15_oil_gas_code'] == "GAS WELL"
    assert rec['wb_h15_type_test_flag'] == "MECHANICAL INTEGRITY TEST"
    assert rec['wb_h15_mech_integ_test_flag'] == "HYDRAULIC"
    
    # Test Raw
    parser_raw = WellBoreParser(convert_values=False)
    wells_raw = list(parser_raw.parse_file(fpath))
    rec_raw = wells_raw[0]['WBH15']
    
    assert rec_raw['wb_h15_status'] == "C"
