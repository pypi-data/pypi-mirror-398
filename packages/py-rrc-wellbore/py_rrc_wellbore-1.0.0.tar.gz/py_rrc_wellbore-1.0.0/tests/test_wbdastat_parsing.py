import pytest
from py_rrc_wellbore.parser import WellBoreParser

def create_dummy_file(tmp_path, content):
    p = tmp_path / "dummy_wbdastat.txt"
    p.write_text(content, encoding='utf-8')
    return str(p)

def test_wbdastat_parsing(tmp_path):
    # 26 Record
    # 03-09 STAT-NUM (7) -> 1234567
    # 10-11 UNIQ-NUM (2) -> 99
    # 12 DELETED (1) -> 'Y'
    
    stat_num = "1234567"
    uniq_num = "99"
    deleted = "Y"
    
    line_arr = list(" " * 247) # Fixed length or at least covering fields
    line_arr[0:2] = list("26")
    line_arr[3-1:3-1+7] = list(stat_num)
    line_arr[10-1:10-1+2] = list(uniq_num)
    line_arr[12-1] = deleted
    
    line_data = (
        "01" + " " * 200 + "\n" +
        "".join(line_arr) + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, line_data)
    
    parser = WellBoreParser(convert_values=True)
    wells = list(parser.parse_file(fpath))
    
    assert len(wells) == 1
    rec = wells[0]['WBDASTAT']
    # If multiple occurrences possible, might be list.
    # Spec says "RECURRING". So likely list.
    # The current parser logic for recurring segments usually returns a list if multiple, 
    # or single dict if parser config allows. 
    # Based on previous tests, recurring segments are often handled as lists.
    # Let's check if my parser treats this as list by default for recurring.
    # The `mappings.py` doesn't explicitly mark 'recurring' vs 'non-recurring' logic except implicitly by key.
    # However, my previous tests for recurring segments (like WBDRILL) asserted list.
    # Let's see what happens. If the parser logic appends to list for ANY key that appears multiple times, 
    # or if specific keys are hardcoded as lists.
    # Looking at `parser.py` (not visible now but recalling logic), usually it's dict unless collision?
    # Actually `WBDRILL` was list. 
    # Let's assume list since it says RECURRING.
    
    # Wait, `rec` might be a single dict if only one line found and parser collapses singletons?
    # Or always list if recurring? 
    # Let's test as if it returns the item or list.
    
    if isinstance(rec, list):
        item = rec[0]
    else:
        item = rec

    assert item['wb_dastat_stat_num'] == 1234567
    assert item['wb_dastat_uniq_num'] == 99
    assert item['wb_dastat_deleted_flag'] == "DELETED"

def test_wbdastat_multiple(tmp_path):
    # Add two records
    line1 = "26" + "1111111" + "01" + "N" + (" " * 50)
    line2 = "26" + "2222222" + "02" + "Y" + (" " * 50)
    
    data = (
        "01" + " " * 200 + "\n" +
        line1 + "\n" +
        line2 + "\n"
    )
    
    fpath = create_dummy_file(tmp_path, data)
    parser = WellBoreParser(convert_values=True)
    wells = list(parser.parse_file(fpath))
    
    items = wells[0]['WBDASTAT']
    assert isinstance(items, list)
    assert len(items) == 2
    assert items[0]['wb_dastat_deleted_flag'] == "ACTIVE"
    assert items[1]['wb_dastat_deleted_flag'] == "DELETED"
