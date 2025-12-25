import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbcompl.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbcompl_parsing(tmp_path):
    # 02 Record
    # Oil Key: Code(1), Dist(2), Lse(5), Well(6) -> Total 14
    # Gas Key: Code(1), RRC(6), Filler(7) -> Total 14
    
    # We will put data that makes sense for both if possible, or distinct to verify overlap.
    # 02 + 0 + 12 (Dist) + 34567 (Lse) + 890123 (Well)
    # Gas view: 0 + 123456 (RRC) + 7890123 (Filler)
    # Let's align them to check redefines.
    
    # Bytes 3-16 (1-based), so indices 2-16.
    # Pos 3: 'O'
    # Pos 4-5: '01'
    # Pos 6-10: '00123'
    # Pos 11-16: 'WELL01'
    
    # Gas View:
    # Pos 3: 'O'
    # Pos 4-9: '010012' (RRC ID)
    
    line_data = (
        "01" + " " * 100 + "\n" + # Root to hold it
        "02" + 
        "O" + "01" + "00123" + "WELL01" +
        # 17: Gas Dist (2) '02'
        "02" +
        # 19: Gas Well (6) 'WELL02'
        "WELL02" +
        # 25: Multi (1) 'M'
        "M" +
        # 26: Suffix (2) '99'
        "99" +
        " " * 200 # Pad
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    compl = wells[0]['WBCOMPL']
    
    # Oil Fields
    assert compl['wb_oil_code'] == 'O'
    assert compl['wb_oil_dist'] == 1
    assert compl['wb_oil_lse_nbr'] == 123
    assert compl['wb_oil_well_nbr'] == 'WELL01'
    
    # Gas Fields (Redefine)
    # Gas ID is 4-9: '010012' -> 10012
    assert compl['wb_gas_code'] == 'O'
    assert compl['wb_gas_rrc_id'] == 10012
    
    # Other Fields
    assert compl['wb_gas_dist'] == 2
    assert compl['wb_gas_well_no'] == 'WELL02'
    assert compl['wb_multi_well_rec_nbr'] == 'M'
    assert compl['wb_api_suffix'] == 99

def test_wbcompl_multiples(tmp_path):
    line_data = (
        "01" + " " * 100 + "\n" +
        "02" + "COMP1" + " " * 100 + "\n" +
        "02" + "COMP2" + " " * 100 + "\n"
    )
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    compls = wells[0]['WBCOMPL']
    assert isinstance(compls, list)
    assert len(compls) == 2
    # Verify raw if extraction fails fallback
    # Since we implemented layouts, these will try key parsing and likely succeed with None/partial data if string is short?
    # Actually invalid string length might throw if not padded.
    # Wrote logic: "slicing beyond end returns empty string". 'int' conversion handles empty string -> None.
    # So it should be fine.
