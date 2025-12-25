"""
Zip handling and filename pattern matching for RRC map data.

This module provides functionality to:
- Process single or multiple .zip files containing RRC GIS data
- Extract County FIPS codes from filenames
- Route unzipped files to appropriate layer parsing logic
"""

import re
import tempfile
import zipfile
from enum import Enum
from pathlib import Path
from typing import Iterator


class LayerType(Enum):
    """Layer types for RRC well data."""
    SURFACE_WELL = "surface"    # well<fips>s.* - Surface Well points
    BOTTOM_WELL = "bottom"      # well<fips>b.* - Bottom Well points
    WELLBORE_ARC = "arc"        # well<fips>l.* - Surface/Bottom Arcs (lines)
    UNKNOWN = "unknown"


# Regex pattern to extract FIPS from filename (e.g., well329.zip → 329)
FIPS_PATTERN = re.compile(r"well(\d+)\.zip", re.IGNORECASE)

# Regex pattern to identify layer type from 8.3 naming convention
LAYER_PATTERN = re.compile(r"well(\d+)([sbl])\.", re.IGNORECASE)


def extract_fips_from_filename(filename: str) -> str | None:
    """
    Extract the County FIPS code from a zip filename.
    
    Args:
        filename: The zip filename (e.g., "well329.zip" or "/path/to/well329.zip")
        
    Returns:
        The FIPS code as a string (e.g., "329"), or None if not found
        
    Examples:
        >>> extract_fips_from_filename("well329.zip")
        '329'
        >>> extract_fips_from_filename("/data/well307.zip")
        '307'
    """
    basename = Path(filename).name
    match = FIPS_PATTERN.match(basename)
    if match:
        return match.group(1)
    return None


def route_layer(filename: str) -> LayerType:
    """
    Determine the layer type from a shapefile component filename.
    
    Uses the 8.3 naming convention:
    - well<fips>s.* → SURFACE_WELL (Surface Well points)
    - well<fips>b.* → BOTTOM_WELL (Bottom Well points)
    - well<fips>l.* → WELLBORE_ARC (Surface/Bottom Arcs)
    
    Args:
        filename: The shapefile component filename (e.g., "well329s.shp")
        
    Returns:
        LayerType enum value indicating the layer type
        
    Examples:
        >>> route_layer("well329s.shp")
        <LayerType.SURFACE_WELL: 'surface'>
        >>> route_layer("well329b.dbf")
        <LayerType.BOTTOM_WELL: 'bottom'>
        >>> route_layer("well329l.shx")
        <LayerType.WELLBORE_ARC: 'arc'>
    """
    basename = Path(filename).name
    match = LAYER_PATTERN.match(basename)
    
    if not match:
        return LayerType.UNKNOWN
    
    layer_suffix = match.group(2).lower()
    
    layer_map = {
        "s": LayerType.SURFACE_WELL,
        "b": LayerType.BOTTOM_WELL,
        "l": LayerType.WELLBORE_ARC,
    }
    
    return layer_map.get(layer_suffix, LayerType.UNKNOWN)


def get_layer_files(extract_dir: Path, layer_type: LayerType) -> dict[str, Path]:
    """
    Get all shapefile component files for a specific layer type.
    
    Args:
        extract_dir: Directory containing extracted shapefile components
        layer_type: The layer type to find files for
        
    Returns:
        Dictionary mapping file extension to Path (e.g., {".shp": Path(...), ".dbf": Path(...)})
    """
    suffix_map = {
        LayerType.SURFACE_WELL: "s",
        LayerType.BOTTOM_WELL: "b",
        LayerType.WELLBORE_ARC: "l",
    }
    
    suffix = suffix_map.get(layer_type)
    if not suffix:
        return {}
    
    files = {}
    for file_path in extract_dir.iterdir():
        if route_layer(file_path.name) == layer_type:
            files[file_path.suffix.lower()] = file_path
    
    return files


def extract_zip(zip_path: str | Path, extract_dir: Path | None = None) -> Path:
    """
    Extract a zip file to a directory.
    
    Args:
        zip_path: Path to the .zip file
        extract_dir: Optional extraction directory. If None, creates a temp directory.
        
    Returns:
        Path to the extraction directory
        
    Raises:
        FileNotFoundError: If the zip file doesn't exist
        zipfile.BadZipFile: If the file is not a valid zip archive
    """
    zip_path = Path(zip_path)
    
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")
    
    if extract_dir is None:
        extract_dir = Path(tempfile.mkdtemp(prefix="rrc_mapdata_"))
    
    extract_dir = Path(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    
    return extract_dir


def ingest_zip(
    zip_path: str | Path,
    convert_values: bool = False,
    cleanup: bool = True,
) -> dict:
    """
    Process a single RRC GIS zip file.
    
    Args:
        zip_path: Path to the .zip file containing shapefile components
        convert_values: If True, convert numeric codes to text descriptions
        cleanup: If True, remove extracted files after processing
        
    Returns:
        Dictionary containing:
        - fips: The county FIPS code
        - layers: Dict of layer type to list of parsed records
        - metadata: Processing metadata
        
    Example:
        >>> result = ingest_zip("well329.zip", convert_values=True)
        >>> print(result["fips"])
        '329'
        >>> print(result["layers"]["surface"])
        [{'APINUM': '423290001234', ...}, ...]
    """
    from .parser import parse_shapefile
    
    zip_path = Path(zip_path)
    fips = extract_fips_from_filename(zip_path.name)
    
    if fips is None:
        raise ValueError(f"Could not extract FIPS code from filename: {zip_path.name}")
    
    extract_dir = extract_zip(zip_path)
    
    try:
        result = {
            "fips": fips,
            "source_file": str(zip_path),
            "layers": {},
            "metadata": {
                "convert_values": convert_values,
            },
        }
        
        # Process each layer type
        for layer_type in [LayerType.SURFACE_WELL, LayerType.BOTTOM_WELL, LayerType.WELLBORE_ARC]:
            layer_files = get_layer_files(extract_dir, layer_type)
            
            if ".shp" in layer_files:
                shp_path = layer_files[".shp"]
                records = parse_shapefile(shp_path, convert_values=convert_values)
                result["layers"][layer_type.value] = records
                result["metadata"][f"{layer_type.value}_count"] = len(records)
        
        return result
        
    finally:
        if cleanup:
            import shutil
            shutil.rmtree(extract_dir, ignore_errors=True)


def ingest_zips(
    zip_paths: list[str | Path],
    convert_values: bool = False,
    cleanup: bool = True,
) -> Iterator[dict]:
    """
    Process multiple RRC GIS zip files.
    
    Args:
        zip_paths: List of paths to .zip files
        convert_values: If True, convert numeric codes to text descriptions
        cleanup: If True, remove extracted files after processing
        
    Yields:
        Dictionary for each processed zip file (see ingest_zip for format)
        
    Example:
        >>> for result in ingest_zips(["well329.zip", "well307.zip"]):
        ...     print(f"Processed county FIPS: {result['fips']}")
    """
    for zip_path in zip_paths:
        yield ingest_zip(zip_path, convert_values=convert_values, cleanup=cleanup)
