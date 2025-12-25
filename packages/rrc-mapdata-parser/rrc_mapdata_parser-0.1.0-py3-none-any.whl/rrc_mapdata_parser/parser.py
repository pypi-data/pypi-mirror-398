"""
Shapefile and DBF record extraction for RRC map data.

This module provides functionality to:
- Parse ESRI shapefiles with geometry and attribute data
- Extract records from DBF attribute tables
- Handle coordinate precision and character encoding
- Optionally convert numeric codes to text descriptions
"""

from decimal import Decimal
from pathlib import Path
from typing import Any

import shapefile
from dbfread import DBF

from .lookups import convert_symnum, convert_reliab


# Character encoding for RRC attribute strings
DEFAULT_ENCODING = "ISO-8859-1"

# Coordinate fields that should maintain double precision
COORDINATE_FIELDS = {"LAT27", "LONG27", "LAT83", "LONG83"}

# API number field variations
API_FIELDS = {"APINUM", "API_NUM", "API10", "API"}

# Relational ID fields for point-to-arc joins
RELATIONAL_FIELDS = {"SURFACE_ID", "SURFACE-ID", "BOTTOM_ID", "BOTTOM-ID"}


def _normalize_field_name(name: str) -> str:
    """
    Normalize field names by replacing hyphens with underscores.
    
    Args:
        name: Original field name
        
    Returns:
        Normalized field name
    """
    return name.replace("-", "_")


def _convert_field_value(
    field_name: str,
    value: Any,
    convert_values: bool = False,
) -> Any:
    """
    Convert a field value, optionally applying code-to-text conversion.
    
    Args:
        field_name: The name of the field
        value: The raw value from the shapefile
        convert_values: If True, convert SYMNUM and RELIAB codes
        
    Returns:
        The converted value
    """
    if value is None:
        return None
    
    # Handle coordinate precision - ensure double precision
    if field_name.upper() in COORDINATE_FIELDS:
        if isinstance(value, (int, float)):
            # Maintain precision by using Decimal then converting to float
            return float(Decimal(str(value)))
        return value
    
    # Handle code conversions when enabled
    if convert_values:
        if field_name.upper() == "SYMNUM":
            return convert_symnum(value)
        elif field_name.upper() == "RELIAB":
            return convert_reliab(value)
    
    # Handle string encoding
    if isinstance(value, bytes):
        try:
            return value.decode(DEFAULT_ENCODING)
        except UnicodeDecodeError:
            return value.decode("utf-8", errors="replace")
    
    return value


def _extract_api_numbers(record: dict) -> dict:
    """
    Extract and normalize API number fields from a record.
    
    The unique identifier is APINUM. This function extracts:
    - api12: 12-digit version (including state code 42)
    - api10: 10-digit version
    - api8: 8-digit version
    
    Args:
        record: The record dictionary
        
    Returns:
        Dictionary with normalized API number fields
    """
    api_data = {}
    
    # Find the primary API number
    api_value = None
    for field in ["APINUM", "API_NUM"]:
        if field in record and record[field]:
            api_value = str(record[field]).strip()
            break
    
    if api_value:
        # Normalize: remove any non-digit characters
        api_digits = "".join(c for c in api_value if c.isdigit())
        
        # Store different precision levels
        if len(api_digits) >= 12:
            api_data["api12"] = api_digits[:12]
            api_data["api10"] = api_digits[2:12]  # Strip state code
            api_data["api8"] = api_digits[2:10]   # Strip state code and suffix
        elif len(api_digits) >= 10:
            api_data["api10"] = api_digits[:10]
            api_data["api8"] = api_digits[:8]
        elif len(api_digits) >= 8:
            api_data["api8"] = api_digits[:8]
    
    return api_data


def parse_dbf(
    dbf_path: str | Path,
    convert_values: bool = False,
    encoding: str = DEFAULT_ENCODING,
) -> list[dict]:
    """
    Parse a DBF file and extract all records.
    
    Args:
        dbf_path: Path to the .dbf file
        convert_values: If True, convert SYMNUM and RELIAB codes to text
        encoding: Character encoding for string fields
        
    Returns:
        List of dictionaries, one per record
        
    Raises:
        FileNotFoundError: If the DBF file doesn't exist
    """
    dbf_path = Path(dbf_path)
    
    if not dbf_path.exists():
        raise FileNotFoundError(f"DBF file not found: {dbf_path}")
    
    records = []
    
    table = DBF(str(dbf_path), encoding=encoding, ignore_missing_memofile=True)
    
    for dbf_record in table:
        record = {}
        
        for field_name, value in dbf_record.items():
            normalized_name = _normalize_field_name(field_name)
            converted_value = _convert_field_value(field_name, value, convert_values)
            record[normalized_name] = converted_value
        
        # Add normalized API numbers
        api_data = _extract_api_numbers(record)
        record.update(api_data)
        
        records.append(record)
    
    return records


def parse_shapefile(
    shp_path: str | Path,
    convert_values: bool = False,
    encoding: str = DEFAULT_ENCODING,
) -> list[dict]:
    """
    Parse a shapefile and extract geometry and attribute data.
    
    Coordinates are maintained at double-precision for LAT27, LONG27,
    LAT83, and LONG83 fields. SURFACE_ID and BOTTOM_ID are extracted
    for point-to-arc joins.
    
    Args:
        shp_path: Path to the .shp file
        convert_values: If True, convert SYMNUM and RELIAB codes to text
        encoding: Character encoding for string fields
        
    Returns:
        List of dictionaries containing:
        - geometry: Dict with type and coordinates
        - All attribute fields from the DBF
        - Normalized API number fields (api12, api10, api8)
        
    Raises:
        FileNotFoundError: If the shapefile doesn't exist
        
    Example:
        >>> records = parse_shapefile("well329s.shp", convert_values=True)
        >>> for rec in records:
        ...     print(f"API: {rec.get('api12')}, Type: {rec.get('SYMNUM')}")
    """
    shp_path = Path(shp_path)
    
    if not shp_path.exists():
        raise FileNotFoundError(f"Shapefile not found: {shp_path}")
    
    records = []
    
    with shapefile.Reader(str(shp_path), encoding=encoding) as sf:
        # Get field names (skip DeletionFlag field at index 0)
        field_names = [field[0] for field in sf.fields[1:]]
        
        for shape_record in sf.iterShapeRecords():
            record = {}
            
            # Extract geometry
            shape = shape_record.shape
            if shape.shapeType == shapefile.POINT:
                record["geometry"] = {
                    "type": "Point",
                    "coordinates": [shape.points[0][0], shape.points[0][1]],
                }
            elif shape.shapeType == shapefile.POLYLINE:
                record["geometry"] = {
                    "type": "LineString",
                    "coordinates": [[p[0], p[1]] for p in shape.points],
                }
            elif shape.shapeType == shapefile.POLYGON:
                record["geometry"] = {
                    "type": "Polygon",
                    "coordinates": [[[p[0], p[1]] for p in shape.points]],
                }
            else:
                record["geometry"] = None
            
            # Extract attributes
            for field_name, value in zip(field_names, shape_record.record):
                normalized_name = _normalize_field_name(field_name)
                converted_value = _convert_field_value(field_name, value, convert_values)
                record[normalized_name] = converted_value
            
            # Add normalized API numbers
            api_data = _extract_api_numbers(record)
            record.update(api_data)
            
            records.append(record)
    
    return records
