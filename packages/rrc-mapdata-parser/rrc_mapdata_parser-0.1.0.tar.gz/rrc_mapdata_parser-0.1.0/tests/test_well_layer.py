"""
Tests for coordinate and attribute verification in well layer parsing.
"""

import pytest
from decimal import Decimal

from rrc_mapdata_parser.parser import (
    _normalize_field_name,
    _convert_field_value,
    _extract_api_numbers,
)
from rrc_mapdata_parser.lookups import (
    convert_symnum,
    convert_reliab,
    WELL_SYMBOLS,
    RELIABILITY_CODES,
)


class TestCoordinatePrecision:
    """Tests for coordinate precision handling."""
    
    def test_lat27_precision(self):
        """Test LAT27 maintains double precision."""
        value = 31.99754321
        result = _convert_field_value("LAT27", value, convert_values=False)
        assert result == pytest.approx(31.99754321, rel=1e-8)
    
    def test_long27_precision(self):
        """Test LONG27 maintains double precision."""
        value = -102.12345678
        result = _convert_field_value("LONG27", value, convert_values=False)
        assert result == pytest.approx(-102.12345678, rel=1e-8)
    
    def test_lat83_precision(self):
        """Test LAT83 maintains double precision."""
        value = 31.99765432
        result = _convert_field_value("LAT83", value, convert_values=False)
        assert result == pytest.approx(31.99765432, rel=1e-8)
    
    def test_long83_precision(self):
        """Test LONG83 maintains double precision."""
        value = -102.12354321
        result = _convert_field_value("LONG83", value, convert_values=False)
        assert result == pytest.approx(-102.12354321, rel=1e-8)
    
    def test_coordinate_none_value(self):
        """Test None coordinate values are preserved."""
        result = _convert_field_value("LAT27", None, convert_values=False)
        assert result is None
    
    def test_coordinate_case_insensitive(self):
        """Test coordinate field matching is case-insensitive."""
        value = 31.12345678
        result = _convert_field_value("lat27", value, convert_values=False)
        assert result == pytest.approx(31.12345678, rel=1e-8)


class TestApiExtraction:
    """Tests for API number extraction and normalization."""
    
    def test_extract_12_digit_api(self):
        """Test extraction of 12-digit API number."""
        record = {"APINUM": "423290001234"}
        result = _extract_api_numbers(record)
        
        assert result["api12"] == "423290001234"
        assert result["api10"] == "3290001234"
        assert result["api8"] == "32900012"
    
    def test_extract_10_digit_api(self):
        """Test extraction of 10-digit API number."""
        record = {"APINUM": "3290001234"}
        result = _extract_api_numbers(record)
        
        assert "api12" not in result
        assert result["api10"] == "3290001234"
        assert result["api8"] == "32900012"
    
    def test_extract_8_digit_api(self):
        """Test extraction of 8-digit API number."""
        record = {"APINUM": "32900012"}
        result = _extract_api_numbers(record)
        
        assert "api12" not in result
        assert "api10" not in result
        assert result["api8"] == "32900012"
    
    def test_extract_api_with_formatting(self):
        """Test API extraction handles formatted numbers."""
        record = {"APINUM": "42-329-00012-34"}
        result = _extract_api_numbers(record)
        
        assert result["api12"] == "423290001234"
    
    def test_extract_api_alternate_field(self):
        """Test API extraction from API_NUM field."""
        record = {"API_NUM": "423290001234"}
        result = _extract_api_numbers(record)
        
        assert result["api12"] == "423290001234"
    
    def test_extract_api_missing(self):
        """Test handling of missing API number."""
        record = {"OTHER_FIELD": "value"}
        result = _extract_api_numbers(record)
        
        assert result == {}
    
    def test_extract_api_empty_string(self):
        """Test handling of empty API string."""
        record = {"APINUM": ""}
        result = _extract_api_numbers(record)
        
        assert result == {}


class TestValueConversion:
    """Tests for SYMNUM and RELIAB code conversion."""
    
    def test_convert_symnum_oil_well(self):
        """Test SYMNUM conversion for oil well."""
        assert convert_symnum(4) == "Oil Well"
    
    def test_convert_symnum_gas_well(self):
        """Test SYMNUM conversion for gas well."""
        assert convert_symnum(5) == "Gas Well"
    
    def test_convert_symnum_dry_hole(self):
        """Test SYMNUM conversion for dry hole."""
        assert convert_symnum(6) == "Dry Hole"
    
    def test_convert_symnum_injection(self):
        """Test SYMNUM conversion for injection well."""
        assert convert_symnum(11) == "Injection/Disposal Well"
    
    def test_convert_symnum_unknown_code(self):
        """Test SYMNUM conversion for unknown code."""
        result = convert_symnum(999)
        assert "Unknown" in result
    
    def test_convert_symnum_none(self):
        """Test SYMNUM conversion for None value."""
        assert convert_symnum(None) == "Unknown"
    
    def test_convert_reliab_wellbore(self):
        """Test RELIAB conversion for wellbore distances."""
        assert convert_reliab(20) == "WELLBORE Distances"
    
    def test_convert_reliab_field_inspection(self):
        """Test RELIAB conversion for field inspection."""
        assert convert_reliab(45) == "Field Inspection by RRC personnel"
    
    def test_convert_reliab_gps(self):
        """Test RELIAB conversion for GPS survey."""
        assert convert_reliab(5) == "GPS Survey"
    
    def test_convert_reliab_unknown_code(self):
        """Test RELIAB conversion for unknown code."""
        result = convert_reliab(999)
        assert "Unknown" in result
    
    def test_convert_reliab_none(self):
        """Test RELIAB conversion for None value."""
        assert convert_reliab(None) == "Unknown"
    
    def test_field_value_symnum_with_convert(self):
        """Test field value conversion with convert_values=True."""
        result = _convert_field_value("SYMNUM", 4, convert_values=True)
        assert result == "Oil Well"
    
    def test_field_value_symnum_without_convert(self):
        """Test field value preserves code with convert_values=False."""
        result = _convert_field_value("SYMNUM", 4, convert_values=False)
        assert result == 4
    
    def test_field_value_reliab_with_convert(self):
        """Test RELIAB field value conversion."""
        result = _convert_field_value("RELIAB", 20, convert_values=True)
        assert result == "WELLBORE Distances"


class TestEncoding:
    """Tests for character encoding handling."""
    
    def test_bytes_to_string_iso88591(self):
        """Test ISO-8859-1 decoding of byte strings."""
        # "Año" in ISO-8859-1
        value = b"A\xf1o"
        result = _convert_field_value("LEASE_NAME", value, convert_values=False)
        assert result == "Año"
    
    def test_regular_string_passthrough(self):
        """Test regular strings pass through unchanged."""
        value = "Normal String"
        result = _convert_field_value("LEASE_NAME", value, convert_values=False)
        assert result == "Normal String"


class TestFieldNameNormalization:
    """Tests for field name normalization."""
    
    def test_normalize_surface_id(self):
        """Test SURFACE-ID normalization."""
        assert _normalize_field_name("SURFACE-ID") == "SURFACE_ID"
    
    def test_normalize_bottom_id(self):
        """Test BOTTOM-ID normalization."""
        assert _normalize_field_name("BOTTOM-ID") == "BOTTOM_ID"
    
    def test_normalize_no_change(self):
        """Test field without hyphen unchanged."""
        assert _normalize_field_name("APINUM") == "APINUM"


class TestLookupDictionaries:
    """Tests for lookup dictionary completeness."""
    
    def test_well_symbols_has_common_codes(self):
        """Test WELL_SYMBOLS contains common codes."""
        required_codes = [4, 5, 6, 11]  # Oil, Gas, Dry, Injection
        for code in required_codes:
            assert code in WELL_SYMBOLS
    
    def test_reliability_codes_has_common_codes(self):
        """Test RELIABILITY_CODES contains common codes."""
        required_codes = [20, 45]  # WELLBORE Distances, Field Inspection
        for code in required_codes:
            assert code in RELIABILITY_CODES
