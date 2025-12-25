"""
Main RRC Mapdata Parser class.

Provides a unified interface for parsing RRC GIS data with support for
multiple layer types: Base, Wells, Surveys, and Pipelines.
"""

from enum import Enum
from pathlib import Path
from typing import Iterator

from .ingest import ingest_zip, ingest_zips, extract_fips_from_filename, LayerType


class DataLayer(Enum):
    """
    Main data layer categories in RRC GIS exports.
    
    Each category contains multiple sub-layers as defined in the RRC
    Digital Map Information specification.
    """
    BASE = "base"           # Airports, Cemeteries, Cities, etc.
    WELLS = "wells"         # Surface, Bottom, Arcs
    SURVEYS = "surveys"     # Lines, Polygons, Bay tracts
    PIPELINES = "pipelines" # Abandoned, Liquid, Gas


class RRCMapdataParser:
    """
    Main parser class for RRC Digital Map Information.
    
    Provides a unified interface for parsing and accessing GIS data from
    RRC zip archives. Currently focused on Wells layer with planned
    expansion to Base, Surveys, and Pipelines.
    
    Attributes:
        convert_values: If True, convert numeric codes to text descriptions
        encoding: Character encoding for attribute strings (default: ISO-8859-1)
    
    Example:
        >>> parser = RRCMapdataParser(convert_values=True)
        >>> result = parser.parse("tests/data/well329.zip")
        >>> wells = result.wells
        >>> print(wells.surface[0]['api12'])
        '423290001234'
    """
    
    def __init__(
        self,
        convert_values: bool = False,
        encoding: str = "ISO-8859-1",
    ):
        """
        Initialize the RRC Mapdata Parser.
        
        Args:
            convert_values: If True, convert SYMNUM and RELIAB codes to text
            encoding: Character encoding for attribute strings
        """
        self.convert_values = convert_values
        self.encoding = encoding
    
    def parse(self, zip_path: str | Path) -> "ParseResult":
        """
        Parse a single RRC GIS zip archive.
        
        Args:
            zip_path: Path to the .zip file
            
        Returns:
            ParseResult object with access to parsed layer data
            
        Raises:
            FileNotFoundError: If the zip file doesn't exist
            ValueError: If FIPS code cannot be extracted from filename
        """
        result = ingest_zip(
            zip_path,
            convert_values=self.convert_values,
            cleanup=True,
        )
        return ParseResult(result)
    
    def parse_many(self, zip_paths: list[str | Path]) -> Iterator["ParseResult"]:
        """
        Parse multiple RRC GIS zip archives.
        
        Args:
            zip_paths: List of paths to .zip files
            
        Yields:
            ParseResult object for each parsed archive
        """
        for result in ingest_zips(
            zip_paths,
            convert_values=self.convert_values,
            cleanup=True,
        ):
            yield ParseResult(result)


class WellsLayer:
    """
    Container for Wells layer data.
    
    Wells data includes:
    - Surface: Surface well point locations (well<fips>s)
    - Bottom: Bottom hole point locations (well<fips>b)
    - Arcs: Lines connecting surface to bottom for directional wells (well<fips>l)
    
    Attributes:
        surface: List of surface well records
        bottom: List of bottom hole records
        arcs: List of arc/line records connecting surface to bottom
    """
    
    def __init__(self, layers: dict):
        """
        Initialize WellsLayer from parsed layer data.
        
        Args:
            layers: Dictionary with 'surface', 'bottom', 'arc' keys
        """
        self.surface: list[dict] = layers.get("surface", [])
        self.bottom: list[dict] = layers.get("bottom", [])
        self.arcs: list[dict] = layers.get("arc", [])
    
    @property
    def surface_count(self) -> int:
        """Number of surface well records."""
        return len(self.surface)
    
    @property
    def bottom_count(self) -> int:
        """Number of bottom hole records."""
        return len(self.bottom)
    
    @property
    def arc_count(self) -> int:
        """Number of arc/line records."""
        return len(self.arcs)
    
    def get_well_by_api(self, api: str, layer: str = "surface") -> dict | None:
        """
        Find a well record by API number.
        
        Args:
            api: API number (8, 10, or 12 digits)
            layer: Which layer to search ('surface', 'bottom', or 'arcs')
            
        Returns:
            Well record dict if found, None otherwise
        """
        records = getattr(self, layer, [])
        api_clean = "".join(c for c in api if c.isdigit())
        
        for record in records:
            # Check all API variants
            for key in ["api12", "api10", "api8", "APINUM", "API", "API10"]:
                if key in record and record[key]:
                    record_api = "".join(c for c in str(record[key]) if c.isdigit())
                    if record_api == api_clean or record_api.endswith(api_clean):
                        return record
        return None


class ParseResult:
    """
    Result container for parsed RRC GIS data.
    
    Provides typed access to different layer categories:
    - wells: WellsLayer with surface, bottom, and arc data
    - base: (Future) BaseLayer for base map features
    - surveys: (Future) SurveysLayer for survey data
    - pipelines: (Future) PipelinesLayer for pipeline data
    
    Attributes:
        fips: County FIPS code extracted from filename
        source_file: Original zip file path
        metadata: Processing metadata
    """
    
    def __init__(self, raw_result: dict):
        """
        Initialize ParseResult from raw ingestion result.
        
        Args:
            raw_result: Dictionary from ingest_zip()
        """
        self._raw = raw_result
        self.fips: str = raw_result.get("fips", "")
        self.source_file: str = raw_result.get("source_file", "")
        self.metadata: dict = raw_result.get("metadata", {})
        
        # Initialize layer containers
        self._wells: WellsLayer | None = None
    
    @property
    def wells(self) -> WellsLayer:
        """Access to Wells layer data."""
        if self._wells is None:
            self._wells = WellsLayer(self._raw.get("layers", {}))
        return self._wells
    
    # Future layer properties (stubs for now)
    @property
    def base(self) -> None:
        """Access to Base layer data. (Not yet implemented)"""
        raise NotImplementedError("Base layer parsing not yet implemented")
    
    @property
    def surveys(self) -> None:
        """Access to Surveys layer data. (Not yet implemented)"""
        raise NotImplementedError("Surveys layer parsing not yet implemented")
    
    @property
    def pipelines(self) -> None:
        """Access to Pipelines layer data. (Not yet implemented)"""
        raise NotImplementedError("Pipelines layer parsing not yet implemented")
    
    def __repr__(self) -> str:
        return f"ParseResult(fips='{self.fips}', source='{self.source_file}')"
