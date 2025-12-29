"""
Format constants for query output formatting.

These constants determine how query results are formatted and what data is included.
"""

# Standard format with essential data
NORMAL = 1

# Data with ID included
DATAID = 2

# Only data, no metadata
JUSTDATA = 3

# Data with ID and timestamps
DATAIDDATE = 4

# Raw database format
RAW = 5

# All related IDs (concept, type, user IDs)
ALLID = 6

# List format
LISTNORMAL = 7

# V2 format variant
DATAV2 = 8
