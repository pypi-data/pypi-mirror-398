"""
Code-to-Text conversion dictionaries for RRC well data.

These mappings are derived from the RRC Digital Map Information manual:
- Appendix A: Well Symbology (SYMNUM)
- Appendix C: Well Reliability (RELIAB)
"""

# Well Symbols (SYMNUM) - Appendix A
# Maps numeric symbol codes to human-readable well type descriptions
WELL_SYMBOLS: dict[int, str] = {
    1: "Location",
    2: "Drilling",
    3: "Permitted Location",
    4: "Oil Well",
    5: "Gas Well",
    6: "Dry Hole",
    7: "Oil Well (Shut-In)",
    8: "Gas Well (Shut-In)",
    9: "Plugged Oil Well",
    10: "Plugged Gas Well",
    11: "Injection/Disposal Well",
    12: "Plugged Dry Hole",
    13: "Multi-Completion Oil Well",
    14: "Multi-Completion Gas Well",
    15: "Cancelled Location",
    16: "Junked & Abandoned",
    17: "Unknown",
    18: "Water Supply Well",
    19: "Injection Well (Shut-In)",
    20: "Brine Mining Well",
    21: "Oil Well (Active)",
    22: "Gas Well (Active)",
    23: "Plugged Injection/Disposal Well",
    24: "SWR 14 Permit",
    25: "Water Well",
    26: "Core Test",
    27: "Cathodic Protection",
}

# Reliability Codes (RELIAB) - Appendix C
# Maps numeric reliability codes to accuracy/source descriptions
RELIABILITY_CODES: dict[int, str] = {
    5: "GPS Survey",
    10: "Digitized from Plat",
    15: "Digitized from Base Map",
    20: "WELLBORE Distances",
    25: "Lease Plat Distances",
    30: "Well Spacing Rule",
    35: "Abstract Center",
    40: "Permit Location",
    45: "Field Inspection by RRC personnel",
    50: "Operator Supplied Coordinates",
    55: "Estimated from Description",
    60: "County Center",
    65: "Unknown/Unverified",
    70: "Railroad Commission Records",
    75: "USGS Topographic Map",
    80: "Aerial Photography",
    85: "Calculated from Survey",
    90: "State Land Office Records",
    95: "Not Located",
}


def convert_symnum(code: int | None) -> str:
    """
    Convert a SYMNUM code to its text description.
    
    Args:
        code: The numeric symbol code from the shapefile
        
    Returns:
        Human-readable well type description, or "Unknown" if code not found
    """
    if code is None:
        return "Unknown"
    return WELL_SYMBOLS.get(code, f"Unknown ({code})")


def convert_reliab(code: int | None) -> str:
    """
    Convert a RELIAB code to its text description.
    
    Args:
        code: The numeric reliability code from the shapefile
        
    Returns:
        Human-readable reliability description, or "Unknown" if code not found
    """
    if code is None:
        return "Unknown"
    return RELIABILITY_CODES.get(code, f"Unknown ({code})")
