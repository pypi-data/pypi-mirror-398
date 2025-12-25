import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbplperf.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbplperf_18_parsing(tmp_path):
    # 18 Record
    # 03 WB-PLUG-PERF-COUNTER (3) -> 001
    # 06 WB-PLUG-FROM-PERF (5) -> 09000
    # 11 WB-PLUG-TO-PERF (5) -> 09100
    # 16 WB-PLUG-OPEN-HOLE-INDICATOR (1) -> "Y"
    
    cnt = "001"
    from_perf = "09000"
    to_perf = "09100"
    ind = "Y"
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "18" + 
        cnt + 
        from_perf + 
        to_perf + 
        ind + 
        (" " * 50) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    # Test Raw
    parser = WellBoreParser(convert_values=False)
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    plperf = wells[0]['WBPLPERF']
    # If recurring, it might be a list if multiple, but single one usually dict unless we force list.
    # Current parser logic: key is segment name. If multiple, list. If single, dict.
    
    assert plperf['wb_plug_perf_counter'] == 1
    assert plperf['wb_plug_from_perf'] == 9000
    assert plperf['wb_plug_to_perf'] == 9100
    assert plperf['wb_plug_open_hole_indicator'] == "Y"
    
    # Test Conversion
    parser_conv = WellBoreParser(convert_values=True)
    wells_conv = list(parser_conv.parse_file(fpath))
    plperf_conv = wells_conv[0]['WBPLPERF']
    assert plperf_conv['wb_plug_open_hole_indicator'] == "YES"
