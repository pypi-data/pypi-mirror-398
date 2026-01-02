"""Module for downloading meteograms as svg from YR and to perform simple modifications on them."""

import asyncio
import xml.etree.ElementTree as ET
from typing import Optional

import aiohttp

# Register namespaces to ensure the output SVG is correctly formatted
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

NAMESPACES = {'svg': 'http://www.w3.org/2000/svg'}

def make_meteogram_transparent(svg_root: ET.Element) -> None:
    """
    Manipulates the meteogram svg by making it transparent.
    """
    # 1. Remove background-color from style attribute in the root <svg>
    if 'style' in svg_root.attrib:
        styles = svg_root.attrib['style'].split(';')
        # Filter out background-color
        new_styles = [s for s in styles if not s.strip().startswith('background-color')]
        if new_styles:
            svg_root.attrib['style'] = ';'.join(new_styles)
        else:
            del svg_root.attrib['style']

    # 2. Remove the background rectangle
    # We look for a rect that matches the original dimensions (782x391) starting at 0,0
    for rect in svg_root.findall('svg:rect', NAMESPACES):
        if (rect.attrib.get('x') == '0' and rect.attrib.get('y') == '0' and
            rect.attrib.get('width') == '782' and rect.attrib.get('height') == '391'):
            svg_root.remove(rect)
            break

def unhide_dark_meteogram_details(svg_root: ET.Element) -> None:
    """
    Manipulates the meteogram svg by changing black color to whiteish.
    """
    symbol_color = "#a2a5b3"
    
    # Helper to replace 'currentColor' in attributes
    def replace_color(element, attribute):
        if element.attrib.get(attribute) == 'currentColor':
            element.attrib[attribute] = symbol_color

    # Iterate over all elements to find specific icons to colorize
    # This replaces the specific regex logic with a safer attribute check
    for elem in svg_root.iter():
        # Logic for specific symbols based on the original regex intent
        # 1. Circles with cy="18"
        if elem.tag.endswith('circle') and elem.attrib.get('cy') == '18':
            replace_color(elem, 'stroke')
        
        # 2. Paths with specific d attributes (starts with M12 or M2.04 or M18)
        if elem.tag.endswith('path'):
            d = elem.attrib.get('d', '')
            if d.startswith('M12') or d.startswith('M18'):
                replace_color(elem, 'stroke')
            elif d.startswith('M2.04'):
                replace_color(elem, 'fill')

    # Finally, replace all remaining 'currentColor' with white
    # We serialize, replace, and re-parse because 'currentColor' could be in many places
    # Alternatively, we could iterate all elements and attributes, but string replacement 
    # is acceptable here for a global "catch-all"
    # Note: This is a hybrid approach. Since we already modified the tree, 
    # we might need to be careful. A safer way is to iterate again:
    for elem in svg_root.iter():
        for key, value in elem.attrib.items():
            if value == 'currentColor':
                elem.attrib[key] = "#FFFFFF"

def crop_meteogram(svg_root: ET.Element) -> None:
    """
    Manipulates the meteogram svg by cropping it to the essentials.
    """
    # 1. Update height and viewBox
    svg_root.attrib['height'] = '300'
    svg_root.attrib['viewBox'] = '0 85 782 300'

    base_y = 363.0

    # 2. Move "Served by" group
    # Find the group with the specific transform
    for g in svg_root.findall('.//svg:g', NAMESPACES):
        if g.attrib.get('transform') == 'translate(612, 22.25)':
            g.attrib['transform'] = f'translate(612, {base_y})'
            
    # 3. Move logos
    # The original code replaced y="24.28" and y="20" globally.
    # These attributes belong to the logo <svg> elements which are siblings to the group above.
    # We iterate over all elements to ensure we catch them, mimicking the global replace.
    for elem in svg_root.iter():
        y_val = elem.attrib.get('y')
        if y_val == '24.28':
            elem.attrib['y'] = str(base_y + 1.79)
        elif y_val == '20':
            elem.attrib['y'] = str(base_y - 2.5)

async def fetch_svg_async(location_id: str, dark: bool = False, crop: bool = False,
                          make_transparent: bool = False, unhide_dark_objects: bool = False,
                          session: Optional[aiohttp.ClientSession] = None) -> str:
    """
    Download a meteogram as a svg.

    Arguments:
    location - the Id of the location.
    dark - download the dark version.
    crop - crop the svg to minimum.
    make_transparent - remove the background color.
    unhide_dark_objects - in dark version; alter black objects to visible color.
    session - optional aiohttp ClientSession to use.

    Returns a string containing the meteogram svg.
    """
    meteogram_url = f'https://www.yr.no/en/content/{location_id}/meteogram.svg'
    if dark:
        meteogram_url += '?mode=dark'

    # Use provided session or create a new one
    if session:
        async with session.get(meteogram_url) as response:
            response.raise_for_status() # Check for HTTP errors
            meteogram_text = await response.text()
    else:
        async with aiohttp.ClientSession() as new_session:
            async with new_session.get(meteogram_url) as response:
                response.raise_for_status()
                meteogram_text = await response.text()

    # Parse XML
    try:
        svg_root = ET.fromstring(meteogram_text)
    except ET.ParseError:
        # Fallback or re-raise if the response wasn't valid XML
        raise ValueError("Downloaded content is not a valid SVG")

    if crop:
        crop_meteogram(svg_root)

    if make_transparent:
        make_meteogram_transparent(svg_root)

    if dark and unhide_dark_objects:
        unhide_dark_meteogram_details(svg_root)

    # Serialize back to string
    return ET.tostring(svg_root, encoding='unicode')

def fetch_svg(location_id: str, dark: bool = False, crop: bool = False,
              make_transparent: bool = False, unhide_dark_objects = False) -> str:
    """
    Download a meteogram as a svg.

    Arguments:
    location - the Id of the location.
    dark - download the dark version.
    crop - crop the svg to minimum.
    make_transparent - remove the background color.
    unhide_dark_objects - in dark version; alter black objects to visible color.

    Returns a string containing the meteogram svg.
    """
    meteogram = asyncio.run(fetch_svg_async(location_id, dark, crop,
                                            make_transparent, unhide_dark_objects))
    return meteogram
