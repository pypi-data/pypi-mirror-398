"""
Tests for zip extraction and FIPS identification.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from rrc_mapdata_parser.ingest import (
    extract_fips_from_filename,
    route_layer,
    LayerType,
    get_layer_files,
)


class TestExtractFipsFromFilename:
    """Tests for FIPS code extraction from filenames."""
    
    def test_extract_fips_basic(self):
        """Test basic FIPS extraction from filename."""
        assert extract_fips_from_filename("well329.zip") == "329"
    
    def test_extract_fips_different_county(self):
        """Test FIPS extraction for different county code."""
        assert extract_fips_from_filename("well307.zip") == "307"
    
    def test_extract_fips_with_path(self):
        """Test FIPS extraction from full path."""
        assert extract_fips_from_filename("/data/rrc/well329.zip") == "329"
    
    def test_extract_fips_case_insensitive(self):
        """Test case insensitivity."""
        assert extract_fips_from_filename("WELL329.ZIP") == "329"
    
    def test_extract_fips_invalid_format(self):
        """Test returns None for invalid filename format."""
        assert extract_fips_from_filename("invalid.zip") is None
    
    def test_extract_fips_not_zip(self):
        """Test returns None for non-zip file."""
        assert extract_fips_from_filename("well329.shp") is None
    
    def test_extract_fips_pathlib(self):
        """Test with pathlib Path object."""
        assert extract_fips_from_filename(Path("well329.zip").name) == "329"


class TestRouteLayer:
    """Tests for layer type routing based on 8.3 naming convention."""
    
    def test_route_surface_layer_shp(self):
        """Test routing surface well layer (.shp)."""
        assert route_layer("well329s.shp") == LayerType.SURFACE_WELL
    
    def test_route_surface_layer_dbf(self):
        """Test routing surface well layer (.dbf)."""
        assert route_layer("well329s.dbf") == LayerType.SURFACE_WELL
    
    def test_route_bottom_layer(self):
        """Test routing bottom well layer."""
        assert route_layer("well329b.shp") == LayerType.BOTTOM_WELL
    
    def test_route_arc_layer(self):
        """Test routing arc/line layer."""
        assert route_layer("well329l.shp") == LayerType.WELLBORE_ARC
    
    def test_route_case_insensitive(self):
        """Test case insensitivity."""
        assert route_layer("WELL329S.SHP") == LayerType.SURFACE_WELL
    
    def test_route_unknown_layer(self):
        """Test unknown layer type."""
        assert route_layer("well329x.shp") == LayerType.UNKNOWN
    
    def test_route_invalid_format(self):
        """Test invalid filename format."""
        assert route_layer("invalid.shp") == LayerType.UNKNOWN
    
    def test_route_with_index_extension(self):
        """Test with .shx index file."""
        assert route_layer("well329s.shx") == LayerType.SURFACE_WELL
    
    def test_route_with_projection(self):
        """Test with .prj projection file."""
        assert route_layer("well329b.prj") == LayerType.BOTTOM_WELL


class TestGetLayerFiles:
    """Tests for getting layer files from extraction directory."""
    
    def test_get_surface_layer_files(self, tmp_path):
        """Test finding surface layer files."""
        # Create mock files
        (tmp_path / "well329s.shp").touch()
        (tmp_path / "well329s.dbf").touch()
        (tmp_path / "well329s.shx").touch()
        (tmp_path / "well329b.shp").touch()  # Different layer
        
        files = get_layer_files(tmp_path, LayerType.SURFACE_WELL)
        
        assert ".shp" in files
        assert ".dbf" in files
        assert ".shx" in files
        assert files[".shp"].name == "well329s.shp"
    
    def test_get_bottom_layer_files(self, tmp_path):
        """Test finding bottom layer files."""
        (tmp_path / "well329b.shp").touch()
        (tmp_path / "well329b.dbf").touch()
        
        files = get_layer_files(tmp_path, LayerType.BOTTOM_WELL)
        
        assert ".shp" in files
        assert files[".shp"].name == "well329b.shp"
    
    def test_get_arc_layer_files(self, tmp_path):
        """Test finding arc layer files."""
        (tmp_path / "well329l.shp").touch()
        
        files = get_layer_files(tmp_path, LayerType.WELLBORE_ARC)
        
        assert ".shp" in files
        assert files[".shp"].name == "well329l.shp"
    
    def test_get_unknown_layer_returns_empty(self, tmp_path):
        """Test unknown layer type returns empty dict."""
        files = get_layer_files(tmp_path, LayerType.UNKNOWN)
        assert files == {}
    
    def test_get_layer_no_matching_files(self, tmp_path):
        """Test returns empty when no matching files."""
        (tmp_path / "well329s.shp").touch()
        
        files = get_layer_files(tmp_path, LayerType.BOTTOM_WELL)
        assert ".shp" not in files


class TestZipExtraction:
    """Tests for zip file extraction functionality."""
    
    def test_extract_zip_creates_directory(self, tmp_path):
        """Test that extraction creates the target directory."""
        import zipfile
        
        # Create a test zip file
        zip_path = tmp_path / "well329.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("well329s.shp", b"dummy content")
        
        from rrc_mapdata_parser.ingest import extract_zip
        
        extract_dir = tmp_path / "extracted"
        result = extract_zip(zip_path, extract_dir)
        
        assert result.exists()
        assert (result / "well329s.shp").exists()
    
    def test_extract_zip_file_not_found(self):
        """Test FileNotFoundError for missing zip file."""
        from rrc_mapdata_parser.ingest import extract_zip
        
        with pytest.raises(FileNotFoundError):
            extract_zip("/nonexistent/well329.zip")
