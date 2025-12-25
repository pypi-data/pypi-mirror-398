"""
Core parsing logic for RRC Well Bore data.
"""

from .mappings import SEGMENT_MAP, LOOKUPS, LAYOUTS

class WellBoreParser:
    def __init__(self, segments_to_parse=None, convert_values=False):
        """
        Initialize the parser.
        
        Args:
            segments_to_parse (list[str] | list[int], optional): List of segment keys (e.g., '01', 1) 
                                                                 or names (e.g., 'root') to include.
                                                                 Defaults to None (parse all).
            convert_values (bool): Whether to convert coded values to descriptions. Defaults to False.
        """
        self.convert_values = convert_values
        self.segments_to_parse = self._normalize_segments(segments_to_parse)

    def _normalize_segments(self, segments):
        """Converts input segments to a set of string keys (e.g., {'01', '02'})."""
        if segments is None:
            return None
        
        normalized = set()
        # Create reverse map for name -> key lookup
        name_to_key = {v: k for k, v in SEGMENT_MAP.items()}
        
        for s in segments:
            s_str = str(s).zfill(2) # Handle integers like 1 -> '01'
            if s_str in SEGMENT_MAP:
                normalized.add(s_str)
            elif s in name_to_key:
                normalized.add(name_to_key[s])
            # If unknown, we can ignore or log. For now, ignoring validly allows flexible loose raw usage.
            
        # Always ensure root '01' is included if we are strict, but logic handles '01' existence check.
        # User might WANT only '02' dumps, but hierarchy depends on '01'.
        # We will track '01' for grouping but only output what's requested in the result dict if strictly filtering output fields.
        # However, typically 'segments_to_parse' implies "keep these". 
        return normalized

    def parse_file(self, file_path):
        """
        Yields well bore dictionaries from the file.
        Each dictionary represents one Well Bore Root (Key 01) and its children.
        """
        current_well = None

        # Detect format
        is_ebcdic = False
        with open(file_path, 'rb') as f:
            first_byte = f.read(1)
            # EBCDIC '0' is 0xF0 (240). ASCII '0' is 0x30 (48).
            # Keys start with numbers, so this is a good check.
            if first_byte and first_byte == b'\xf0':
                is_ebcdic = True

        if is_ebcdic:
            # EBCDIC Parsing: Fixed 247 byte records
            with open(file_path, 'rb') as f:
                content = f.read().decode('cp037', errors='replace')
                
            record_length = 247
            for i in range(0, len(content), record_length):
                line = content[i : i + record_length]
                # Pad if short (e.g. last record?)
                if len(line) < record_length:
                    line = line.ljust(record_length)
                
                # Logic copied from text loop
                if not line.strip():
                    continue

                key = line[:2]
                if key not in SEGMENT_MAP:
                     continue

                segment_name = SEGMENT_MAP[key]
                
                should_include = self.segments_to_parse is None or key in self.segments_to_parse


                if key == '01':
                    # Yield previous well if it exists
                    if current_well:
                        yield current_well
                    
                    # Start new well
                    current_well = {}
                    if should_include:
                         current_well[segment_name] = self._parse_line_data(key, line)
                
                else:
                    # Child segment
                    if current_well is not None and should_include:
                        data = self._parse_line_data(key, line)
                        
                        # Handle Multiples
                        if segment_name in current_well:
                            # If it's the second time we see it, convert to list if not already
                            if isinstance(current_well[segment_name], list):
                                current_well[segment_name].append(data)
                            else:
                                # Convert existing single dict to list
                                first_item = current_well[segment_name]
                                current_well[segment_name] = [first_item, data]
                        else:
                            current_well[segment_name] = data

        else:
            # ASCII Text Parsing (Line Based)
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if not line.strip():
                        continue
                        
                    key = line[:2]
                    if key not in SEGMENT_MAP:
                         # Skip unknown segments or invalid lines
                        continue

                    segment_name = SEGMENT_MAP[key]

                    # Check filtering
                    should_include = self.segments_to_parse is None or key in self.segments_to_parse


                    if key == '01':
                        # Yield previous well if it exists
                        if current_well:
                            yield current_well
                        
                        # Start new well
                        current_well = {}
                        if should_include:
                             current_well[segment_name] = self._parse_line_data(key, line)
                    
                    else:
                        # Child segment
                        if current_well is not None and should_include:
                            data = self._parse_line_data(key, line)
                            
                            # Handle Multiples
                            if segment_name in current_well:
                                # If it's the second time we see it, convert to list if not already
                                if isinstance(current_well[segment_name], list):
                                    current_well[segment_name].append(data)
                                else:
                                    # Convert existing single dict to list
                                    first_item = current_well[segment_name]
                                    current_well[segment_name] = [first_item, data]
                            else:
                                current_well[segment_name] = data

        # Yield last one
        if current_well:
            yield current_well

    def _parse_line_data(self, key, line):
        """
        Orchestrates extracting data and applying conversions.
        """
        segment_name = SEGMENT_MAP[key]
        data = self._extract_data(key, line)
        
        if self.convert_values:
            self._apply_conversions(segment_name, data)
            
        return data

    def _extract_data(self, key, line):
        """
        Extracts raw data from line based on LAYOUTS.
        """
        if key not in LAYOUTS:
            # Fallback parsing: just return whole line as 'raw_record'
            return {'raw_record': line.strip()}
        
        layout = LAYOUTS[key]
        data = {}
        
        # Ensure line is padded if short, though typically file lines are fixed width.
        # But slicing beyond end returns empty string, so it's safeish.
        
        for start_1_based, length, field_type, field_name in layout:
            start_idx = start_1_based - 1
            end_idx = start_idx + length
            
            raw_val = line[start_idx:end_idx]
            
            if field_type == 'int':
                try:
                    if raw_val.strip():
                        data[field_name] = int(raw_val)
                    else:
                        data[field_name] = None
                except ValueError:
                    data[field_name] = raw_val # Retain raw if conversion fails
            else:
                data[field_name] = raw_val
                
        return data

    def _apply_conversions(self, segment_name, data):
        """
        Converts codes to descriptions using LOOKUPS.
        """
        if segment_name not in LOOKUPS:
            return

        seg_lookups = LOOKUPS[segment_name]
        for field, value in data.items():
            if field in seg_lookups:
                # If the value matches a code, replace it
                # Note: This requires 'data' to have the extracted fields, not just 'raw_record'.
                # For prototype, we will skip unless we extract fields.
                if value in seg_lookups[field]:
                    data[field] = seg_lookups[field][value]
