import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbplug.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbplug_parsing_raw(tmp_path):
    # 14 Record
    # 03 WB-DATE-W3-FILED (8) -> 20230101
    # 56 WB-PLUG-MUD-FILLED (1) -> "Y"
    # 131 WB-PLUG-TYPE-LOG (1) -> "E"
    # 137 WB-PLUG-FROM-UWQP-1 (5) -> 00100
    # 142 WB-PLUG-TO-UWQP-1 (5) -> 00200
    
    date_w3 = "20230101"
    mud_filled = "Y"
    type_log = "E"
    from_1 = "00100"
    to_1 = "00200"
    
    # Needs padding to position 142+5 = 147 at least.
    # W3 starts at 3.
    # Mud filled at 56.
    # Type log at 131.
    # From1 at 137.
    # To1 at 142.
    
    # Filler calc:
    # 01-02: Key
    # 03-10: Date
    # 11-55: Filler (56-11 = 45 bytes)
    # 56: Mud
    # 57-130: Filler (131-57 = 74 bytes)
    # 131: Type Log
    # 132-136: Filler (137-132 = 5 bytes)
    # 137-141: From 1
    # 142-146: To 1
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "14" + 
        date_w3 + 
        (" " * 45) + 
        mud_filled + 
        (" " * 74) + 
        type_log + 
        (" " * 5) + 
        from_1 + 
        to_1 + 
        (" " * 50) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    # Test Raw
    parser = WellBoreParser(convert_values=False)
    wells = list(parser.parse_file(fpath))
    assert len(wells) == 1
    plug = wells[0]['WBPLUG']
    
    assert plug['wb_date_w3_filed'] == 20230101
    assert plug['wb_plug_mud_filled'] == "Y"
    assert plug['wb_plug_type_log'] == "E"
    assert plug['wb_plug_from_uwqp_1'] == 100
    assert plug['wb_plug_to_uwqp_1'] == 200

def test_wbplug_parsing_converted(tmp_path):
    # Same data, check conversion
    date_w3 = "20230101"
    mud_filled = "N"
    type_log = "R" # Radioactivity
    from_1 = "00100"
    to_1 = "00200"
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "14" + 
        date_w3 + 
        (" " * 45) + 
        mud_filled + 
        (" " * 74) + 
        type_log + 
        (" " * 5) + 
        from_1 + 
        to_1 + 
        (" " * 50) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser(convert_values=True)
    wells = list(parser.parse_file(fpath))
    plug = wells[0]['WBPLUG']
    
    assert plug['wb_plug_mud_filled'] == "NO"
    assert plug['wb_plug_type_log'] == "RADIOACTIVITY"
