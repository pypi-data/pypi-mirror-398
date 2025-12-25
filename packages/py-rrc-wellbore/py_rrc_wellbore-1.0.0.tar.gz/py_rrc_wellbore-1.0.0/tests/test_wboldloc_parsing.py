import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wboldloc.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wboldloc_parsing(tmp_path):
    # 12 Record
    # 03 WB-LEASE-NAME (32) -> "TEST LEASE"
    # 35 WB-SEC-BLK-SURVEY-LOC (52) -> "SEC 1 BLK 2 SUR 3"
    # 87 WB-WELL-LOC-MILES (4) -> 0010
    # 91 WB-WELL-LOC-DIRECTION (6) -> "NORTH "
    # 97 WB-WELL-LOC-NEAREST-TOWN (13) -> "MIDLAND      "
    # 138 WB-DIST-FROM-SURVEY-LINES (28) -> "600 FN 600 FE               "
    # 166 WB-DIST-DIRECT-NEAR-WELL (28) -> "1200 FROM PROPOSED LOC      "
    
    lease = "TEST LEASE".ljust(32)
    sec_blk = "SEC 1 BLK 2 SUR 3".ljust(52)
    miles = "0010"
    direction = "NORTH".ljust(6)
    town = "MIDLAND".ljust(13)
    # Filler between town (110) and dist lines (138) is 28 bytes
    filler1 = " " * 28 
    # Actually town ends at 97+13=110. Dist starts at 138. Gap = 138-110 = 28 bytes. Correct.
    
    dist_lines = "600 FN 600 FE".ljust(28)
    dist_well = "1200 FROM PROPOSED LOC".ljust(28)
    
    # Construct line. 
    # Positions 1-based:
    # 1-2: Key
    # 3-34: Lease
    # 35-86: Sec Blk
    # 87-90: Miles
    # 91-96: Direction
    # 97-109: Town
    # 110-137: Filler (28)
    # 138-165: Dist Lines
    # 166-193: Dist Well
    
    line_data = (
        "01" + " " * 100 + "\n" +
        "12" + 
        lease + 
        sec_blk + 
        miles + 
        direction +
        town + 
        filler1 + 
        dist_lines + 
        dist_well + 
        " " * 100
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    oldloc = wells[0]['WBOLDLOC']
    
    assert oldloc['wb_lease_name'].strip() == "TEST LEASE"
    assert oldloc['wb_sec_blk_survey_loc'].strip() == "SEC 1 BLK 2 SUR 3"
    assert oldloc['wb_well_loc_miles'] == 10
    assert oldloc['wb_well_loc_direction'].strip() == "NORTH"
    assert oldloc['wb_well_loc_nearest_town'].strip() == "MIDLAND"
    assert oldloc['wb_dist_from_survey_lines'].strip() == "600 FN 600 FE"
    assert oldloc['wb_dist_direct_near_well'].strip() == "1200 FROM PROPOSED LOC"
