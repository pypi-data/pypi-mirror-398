from typing import Optional, Union
import datetime

def format_date(val: Union[str, datetime.date, None]) -> Optional[str]:
    """
    Format date value to ISO string (YYYY-MM-DD).
    Handles 'YYYYMMDD' strings or datetime.date objects.
    """
    if not val:
        return None
        
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.strftime("%Y-%m-%d")
        
    val_str = str(val).strip()
    
    # Handle '00000000' or empty
    if not val_str or val_str == "00000000":
        return None
        
    # If 8 digits YYYYMMDD
    if len(val_str) == 8 and val_str.isdigit():
         return f"{val_str[:4]}-{val_str[4:6]}-{val_str[6:]}"
         
    return val_str

def construct_api_number(county_code: Union[str, int], unique_id: Union[str, int]) -> str:
    return f"{int(county_code):03d}-{int(unique_id):05d}"
