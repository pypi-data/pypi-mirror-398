from typing import Iterator, Dict, Any
from dbfread import DBF
from .utils import format_date

class RRCStatewideParser:
    """
    Parser for Texas RRC Statewide API Data in DBF format.
    Wraps dbfread to provide normalized records.
    """

    def __init__(self, dbf_path: str, encoding: str = "iso-8859-1"):
        """
        Initialize the parser.
        
        Args:
            dbf_path: Path to the .dbf file.
            encoding: Character encoding of the DBF file (default: iso-8859-1).
        """
        self.dbf_path = dbf_path
        self.encoding = encoding

    def get_fields(self) -> list[str]:
        """
        Get the list of normalized field names available in the DBF.
        """
        table = DBF(self.dbf_path, encoding=self.encoding, char_decode_errors='replace', load=False)
        # DBF field names are usually uppercase, but we force normalization logic here to match _normalize_record
        return [f.upper() for f in table.field_names]

    def parse(self) -> Iterator[Dict[str, Any]]:
        """
        Yields normalized records from the DBF file.
        
        Returns:
            Iterator of dictionaries containing record data.
        """
        # load=False to stream records
        table = DBF(self.dbf_path, encoding=self.encoding, char_decode_errors='replace', load=False)
        
        for record in table:
            yield self._normalize_record(record)

    def _normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize raw DBF record fields.
        Upper-cases keys and applies formatting helpers where applicable.
        """
        data = dict(record)
        # Normalize keys to uppercase
        data = {k.upper(): v for k, v in data.items()}
        
        # Helper: Ensure date fields are formatted if they exist as strings
        # Based on MAF016 docs: COMPLETION_DATE, PLUG_DATE
        # Observed headers: COMPLETION, PLUG_DATE
        for date_field in ['COMPLETION_DATE', 'COMPLETION', 'PLUG_DATE', 'PERMIT_DATE']: 
             # Note: PERMIT_DATE isn't in MAF016 but might be common. MAF016 has PLUG_DATE, COMPLETION_DATE.
             # MAF016 field names: 
             # MAF016-COMPLETION-DATE -> COMPLETION_DATE? DBF field names usually truncated to 10 chars.
             # Likely: COMP_DATE, PLUG_DATE. We'll check for keys containing date or specific known ones.
             
             # If exact key exists:
             if date_field in data:
                 data[date_field] = format_date(data[date_field])
                 
        return data
