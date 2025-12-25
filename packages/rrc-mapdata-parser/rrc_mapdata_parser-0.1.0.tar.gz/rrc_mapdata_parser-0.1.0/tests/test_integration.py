"""
Integration tests using real RRC sample data.

These tests require tests/data/well329.zip to be present.
They will be skipped if the sample file is not available.
"""

import pytest
from pathlib import Path

from rrc_mapdata_parser import RRCMapdataParser, ParseResult, WellsLayer, DataLayer


class TestRRCMapdataParser:
    """Tests for the main RRCMapdataParser class."""
    
    def test_parser_instantiation(self):
        """Test parser can be created with default settings."""
        parser = RRCMapdataParser()
        assert parser.convert_values is False
        assert parser.encoding == "ISO-8859-1"
    
    def test_parser_with_convert_values(self):
        """Test parser with convert_values enabled."""
        parser = RRCMapdataParser(convert_values=True)
        assert parser.convert_values is True
    
    def test_parse_returns_parse_result(self, require_sample_data, sample_well_zip):
        """Test parse() returns a ParseResult object."""
        parser = RRCMapdataParser()
        result = parser.parse(sample_well_zip)
        
        assert isinstance(result, ParseResult)
        assert result.fips == "329"  # Midland County
    
    def test_parse_with_string_path(self, require_sample_data, sample_well_zip):
        """Test parse() works with string path."""
        parser = RRCMapdataParser()
        result = parser.parse(str(sample_well_zip))
        
        assert isinstance(result, ParseResult)
    
    def test_parse_many(self, require_sample_data, sample_well_zip):
        """Test parse_many() yields ParseResult objects."""
        parser = RRCMapdataParser()
        results = list(parser.parse_many([sample_well_zip]))
        
        assert len(results) == 1
        assert isinstance(results[0], ParseResult)


class TestParseResult:
    """Tests for ParseResult container."""
    
    def test_wells_property(self, require_sample_data, sample_well_zip):
        """Test wells property returns WellsLayer."""
        parser = RRCMapdataParser()
        result = parser.parse(sample_well_zip)
        
        assert isinstance(result.wells, WellsLayer)
    
    def test_fips_extraction(self, require_sample_data, sample_well_zip):
        """Test FIPS code is correctly extracted."""
        parser = RRCMapdataParser()
        result = parser.parse(sample_well_zip)
        
        assert result.fips == "329"
    
    def test_source_file_stored(self, require_sample_data, sample_well_zip):
        """Test source file path is stored."""
        parser = RRCMapdataParser()
        result = parser.parse(sample_well_zip)
        
        assert "well329.zip" in result.source_file
    
    def test_base_layer_not_implemented(self, require_sample_data, sample_well_zip):
        """Test base layer raises NotImplementedError."""
        parser = RRCMapdataParser()
        result = parser.parse(sample_well_zip)
        
        with pytest.raises(NotImplementedError):
            _ = result.base
    
    def test_surveys_layer_not_implemented(self, require_sample_data, sample_well_zip):
        """Test surveys layer raises NotImplementedError."""
        parser = RRCMapdataParser()
        result = parser.parse(sample_well_zip)
        
        with pytest.raises(NotImplementedError):
            _ = result.surveys
    
    def test_pipelines_layer_not_implemented(self, require_sample_data, sample_well_zip):
        """Test pipelines layer raises NotImplementedError."""
        parser = RRCMapdataParser()
        result = parser.parse(sample_well_zip)
        
        with pytest.raises(NotImplementedError):
            _ = result.pipelines


class TestWellsLayer:
    """Tests for WellsLayer data container."""
    
    def test_surface_wells_loaded(self, require_sample_data, sample_well_zip):
        """Test surface wells are loaded."""
        parser = RRCMapdataParser()
        result = parser.parse(sample_well_zip)
        
        wells = result.wells
        assert wells.surface_count > 0
        assert len(wells.surface) == wells.surface_count
    
    def test_bottom_wells_loaded(self, require_sample_data, sample_well_zip):
        """Test bottom wells are loaded (may be empty for vertical wells)."""
        parser = RRCMapdataParser()
        result = parser.parse(sample_well_zip)
        
        wells = result.wells
        # Bottom wells may be empty - just verify attribute exists
        assert isinstance(wells.bottom, list)
        assert wells.bottom_count == len(wells.bottom)
    
    def test_arcs_loaded(self, require_sample_data, sample_well_zip):
        """Test arcs are loaded (for directional wells)."""
        parser = RRCMapdataParser()
        result = parser.parse(sample_well_zip)
        
        wells = result.wells
        # Arcs may be empty - just verify attribute exists
        assert isinstance(wells.arcs, list)
        assert wells.arc_count == len(wells.arcs)
    
    def test_surface_well_has_coordinates(self, require_sample_data, sample_well_zip):
        """Test surface wells have coordinate data."""
        parser = RRCMapdataParser()
        result = parser.parse(sample_well_zip)
        
        if result.wells.surface_count > 0:
            well = result.wells.surface[0]
            # Check for geometry or coordinate fields
            has_coords = (
                "geometry" in well or
                "LAT27" in well or
                "LONG27" in well
            )
            assert has_coords, f"Well should have coordinates: {list(well.keys())}"
    
    def test_surface_well_has_api(self, require_sample_data, sample_well_zip):
        """Test surface wells have API number."""
        parser = RRCMapdataParser()
        result = parser.parse(sample_well_zip)
        
        if result.wells.surface_count > 0:
            well = result.wells.surface[0]
            # Check for any API variant
            has_api = any(
                key in well for key in ["api12", "api10", "api8", "APINUM", "API"]
            )
            assert has_api, f"Well should have API: {list(well.keys())}"
    
    def test_get_well_by_api(self, require_sample_data, sample_well_zip):
        """Test finding well by API number."""
        parser = RRCMapdataParser()
        result = parser.parse(sample_well_zip)
        
        wells = result.wells
        if wells.surface_count > 0:
            # Get first well's API and search for it
            first_well = wells.surface[0]
            api = first_well.get("api12") or first_well.get("api10") or first_well.get("api8")
            
            if api:
                found = wells.get_well_by_api(api, "surface")
                assert found is not None


class TestValueConversion:
    """Tests for SYMNUM and RELIAB code conversion."""
    
    def test_symnum_not_converted_by_default(self, require_sample_data, sample_well_zip):
        """Test SYMNUM codes remain numeric by default."""
        parser = RRCMapdataParser(convert_values=False)
        result = parser.parse(sample_well_zip)
        
        if result.wells.surface_count > 0:
            well = result.wells.surface[0]
            if "SYMNUM" in well and well["SYMNUM"] is not None:
                assert isinstance(well["SYMNUM"], (int, float))
    
    def test_symnum_converted_when_enabled(self, require_sample_data, sample_well_zip):
        """Test SYMNUM codes are converted to text when enabled."""
        parser = RRCMapdataParser(convert_values=True)
        result = parser.parse(sample_well_zip)
        
        if result.wells.surface_count > 0:
            well = result.wells.surface[0]
            if "SYMNUM" in well and well["SYMNUM"] is not None:
                # Should now be a string description
                assert isinstance(well["SYMNUM"], str)


class TestDataLayer:
    """Tests for DataLayer enum."""
    
    def test_data_layer_values(self):
        """Test DataLayer enum has expected values."""
        assert DataLayer.BASE.value == "base"
        assert DataLayer.WELLS.value == "wells"
        assert DataLayer.SURVEYS.value == "surveys"
        assert DataLayer.PIPELINES.value == "pipelines"
