import pytest
import os
from pathlib import Path
from rrc_statewide_api import RRCStatewideParser

# Define path to real data
REAL_DBF_PATH = Path(__file__).parent / "data/api329.dbf"

@pytest.mark.skipif(not REAL_DBF_PATH.exists(), reason="api329.dbf not found")
def test_parser_oil_lease_num():
    """Verify that OIL_LEASE_NUM is synthesized correctly."""
    
    parser = RRCStatewideParser(str(REAL_DBF_PATH))
    records = list(parser.parse())
    
    found_oil_lease = False
    
    for record in records:
        if record.get("OIL_GAS_CODE") == "O":
            # Check logic for Oil wells
            assert "OIL_LEASE_NUM" in record, "Missing OIL_LEASE_NUM key"
            assert record["OIL_LEASE_NUM"] is not None
            assert record["GAS_RRCID"] is None
            assert record["LEASE_NUMBER"] == record["OIL_LEASE_NUM"]
            found_oil_lease = True
            
        elif record.get("OIL_GAS_CODE") == "G":
             # Check logic for Gas wells if any exist in this sample
             assert record["GAS_RRCID"] is not None
             assert record["OIL_LEASE_NUM"] is None
             assert record["LEASE_NUMBER"] == record["GAS_RRCID"]
             
    assert found_oil_lease, "No Oil records found in api329.dbf to test"

def test_parser_field_normalization():
    """Verify field name normalization (e.g. OIL_GAS_CO -> OIL_GAS_CODE)."""
    parser = RRCStatewideParser(str(REAL_DBF_PATH))
    # We can inspect the first record
    for record in parser.parse():
        assert "OIL_GAS_CODE" in record, "Expected OIL_GAS_CODE to be present (renamed from OIL_GAS_CO)"
        assert "OIL_GAS_CO" not in record, "OIL_GAS_CO should be removed"
        break
