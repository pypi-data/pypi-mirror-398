"""
RRC Mapdata Parser

A Python module to ingest and process Texas Railroad Commission (RRC)
Digital Map Information from .zip archives containing ESRI shapefile components.
"""

__version__ = "0.1.0"

from .ingest import ingest_zip, ingest_zips, extract_fips_from_filename, route_layer, LayerType
from .parser import parse_shapefile, parse_dbf
from .lookups import WELL_SYMBOLS, RELIABILITY_CODES, convert_symnum, convert_reliab
from .rrc_parser import RRCMapdataParser, ParseResult, WellsLayer, DataLayer

__all__ = [
    "__version__",
    # Main Parser Class
    "RRCMapdataParser",
    "ParseResult",
    "WellsLayer",
    "DataLayer",
    # Ingestion
    "ingest_zip",
    "ingest_zips",
    "extract_fips_from_filename",
    "route_layer",
    "LayerType",
    # Parsing
    "parse_shapefile",
    "parse_dbf",
    # Lookups
    "WELL_SYMBOLS",
    "RELIABILITY_CODES",
    "convert_symnum",
    "convert_reliab",
]
