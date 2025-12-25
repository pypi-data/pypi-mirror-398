import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbplname.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbplname_parsing(tmp_path):
    # 19 Record
    # 03 WB-PLUG-FIELD-NO (8) -> 12345678
    # 11 WB-PLUG-FIELD-NAME (32) -> "TEST FIELD NAME"
    # 43 WB-PLUG-OPER-NO (6) -> "123456"
    # 49 WB-PLUG-OPER-NAME (32) -> "TEST OPERATOR NAME"
    # 81 WB-PLUG-LEASE-NAME (32) -> "TEST LEASE NAME"
    
    f_no = "12345678"
    f_name = "TEST FIELD NAME".ljust(32)
    o_no = "123456"
    o_name = "TEST OPERATOR NAME".ljust(32)
    l_name = "TEST LEASE NAME".ljust(32)
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "19" + 
        f_no + 
        f_name + 
        o_no + 
        o_name + 
        l_name + 
        (" " * 100) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser()
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    plname = wells[0]['WBPLNAME']
    
    assert plname['wb_plug_field_no'] == 12345678
    assert plname['wb_plug_field_name'].strip() == "TEST FIELD NAME"
    assert plname['wb_plug_oper_no'] == "123456"
    assert plname['wb_plug_oper_name'].strip() == "TEST OPERATOR NAME"
    assert plname['wb_plug_lease_name'].strip() == "TEST LEASE NAME"
