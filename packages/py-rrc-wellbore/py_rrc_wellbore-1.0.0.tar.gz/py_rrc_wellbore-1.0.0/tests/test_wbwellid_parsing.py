import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbwellid.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbwellid_oil_parsing(tmp_path):
    # 21 Record - Oil
    # 03 WB-OIL 'O' (1)
    # 04 WB-DISTRICT 08 (2)
    # 06 WB-LEASE 12345 (5)
    # 11 WB-WELL "123456" (6)
    
    oil_flag = "O"
    dist = "08"
    lease = "12345"
    well = "123456"
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "21" + 
        oil_flag + 
        dist + 
        lease + 
        well + 
        (" " * 100) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    wellid = wells[0]['WBWELLID']
    # Checking as single dict
    
    assert wellid['wb_oil_info_oil'] == "O"
    assert wellid['wb_oil_info_district'] == 8
    assert wellid['wb_oil_info_lease_number'] == 12345
    assert wellid['wb_oil_info_well_number'] == "123456"

def test_wbwellid_gas_parsing(tmp_path):
    # 21 Record - Gas
    # 03 WB-GAS 'G' (1)
    # 04 WB-RRCID 123456 (6)
    
    gas_flag = "G"
    rrcid = "123456"
    
    # 11-16 (old well number pos) might be spaces or garbage
    filler = " " * 6
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "21" + 
        gas_flag + 
        rrcid + 
        filler + 
        (" " * 100) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    wellid = wells[0]['WBWELLID']
    
    assert wellid['wb_gas_info_gas'] == "G"
    assert wellid['wb_gas_info_rrcid'] == 123456
