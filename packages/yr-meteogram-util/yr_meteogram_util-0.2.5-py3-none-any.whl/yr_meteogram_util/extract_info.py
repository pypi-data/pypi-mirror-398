"""Module for extracting information from meteogram svgs downloaded from YR."""

import xml.etree.ElementTree as ET
import re

def get_location_name(meteogram: str) -> str:
    """
    Extracts the location name from a meteogram.
    """
    try:
        root = ET.fromstring(meteogram)
        # The title tag usually contains "Weather forecast for Location"
        # We use the namespace map defined in fetch.py or locally
        title_element = root.find('{http://www.w3.org/2000/svg}title')
        
        if title_element is not None and title_element.text:
            # Extract "Location" from "Weather forecast for Location"
            match = re.search(r'Weather\s+forecast\s+for\s+(.*)', title_element.text)
            if match:
                return match.group(1)
                
    except ET.ParseError:
        pass
        
    # Fallback to regex if XML parsing fails or structure is unexpected
    match = re.search(r'Weather\s+forecast\s+for\s+(.*)', meteogram)
    if match:
        return match.group(1)
    
    return "Unknown Location"
