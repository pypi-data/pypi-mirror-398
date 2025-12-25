import pytest
import os
from pathlib import Path
from rrc_statewide_api import RRCStatewideParser

# Define path to real data
REAL_DBF_PATH = Path(__file__).parent / "data/api329.dbf"

@pytest.mark.skipif(not REAL_DBF_PATH.exists(), reason="api329.dbf not found")
def test_parser_real_data():
    """Verify parser works with real api329.dbf file."""
    
    parser = RRCStatewideParser(str(REAL_DBF_PATH))
    records = list(parser.parse())
    
    # Check that we parsed some records
    assert len(records) > 0, "No records parsed from api329.dbf"
    
    first = records[0]
    
    # Print first record keys to help debugging if needed
    print(f"Record keys: {first.keys()}")
    
    # Verify expected columns exist (based on MAF016/DBF knowledge)
    # We normalized keys to UPPERCASE in parser.
    # Common fields: API_NUM, LEASE_NAME, DIST, CTY
    
    # Note: DBF column names are often short (10 chars max).
    # 'API_NUM' might be just 'API', 'LEASE_NAME' -> 'LSE_NAM' or similar. 
    # But let's check for at least ONE we are reasonably sure of or check simply that we got data.
    
    # If the parser normalizes keys, we check for uppercase.
    assert any("API" in k for k in first.keys()), "Expected API-related column in keys"
    
    # Check date normalization if COMPLETION is present and not empty
    if "COMPLETION" in first and first["COMPLETION"]:
        # Should be YYYY-MM-DD (10 chars) if valid
        assert len(first["COMPLETION"]) == 10, f"Date not normalized: {first['COMPLETION']}"

def test_key_normalization():
    """Test that parser upper-cases keys correctly using the real file."""
    if not REAL_DBF_PATH.exists():
        pytest.skip("api329.dbf missing")
        
    parser = RRCStatewideParser(str(REAL_DBF_PATH))
    # Peek at first record
    records = iter(parser.parse())
    try:
        first = next(records)
        for k in first.keys():
            assert k == k.upper(), f"Key {k} is not uppercase"
    except StopIteration:
        pytest.fail("Empty DBF file")

def test_get_fields():
    """Verify get_fields returns the list of columns."""
    if not REAL_DBF_PATH.exists():
        pytest.skip("api329.dbf missing")
        
    parser = RRCStatewideParser(str(REAL_DBF_PATH))
    fields = parser.get_fields()
    
    assert len(fields) > 0
    assert "API_NUM" in [f.replace('_', '').replace('NUM', '').replace('ID', '') for f in fields] or "APINUM" in fields
    # Based on previous run keys: ['ABSTRACT', 'APINUM', 'BLOCK', 'COMPLETION', ...]
    assert "APINUM" in fields
    assert "LEASE_NAME" in fields or "LEASENAME" in fields or "LEASE_NAM" in fields
    # previous run: LEASE_NAME



