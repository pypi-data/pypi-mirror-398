# RRC Statewide API Parser

A Python library for parsing and processing the Texas Railroad Commission (RRC) **Statewide API Data** provided in dBase (`.dbf`) format.

## Features
- Efficient parsing of legacy `.dbf` files using `dbfread`.
- Automatic handling of character encoding (`ISO-8859-1`).
- Standardized mapping and normalization of date fields.
- Helper utilities for RRC-specific data formatting.

## Installation

```bash
pip install rrc-statewide-api
```

## Usage

```python
from rrc_statewide_api import RRCStatewideParser

parser = RRCStatewideParser("path/to/file.dbf")

for record in parser.parse():
    print(record['API_NUM'], record['LEASE_NAME'])
```
