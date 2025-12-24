import pandas as pd
from importlib.resources import files
from io import StringIO

# Load CSVs using importlib.resources 
def _load_csv(filename):
    """Load CSV file from package data directory"""
    csv_content = files('pybrsa.data').joinpath(filename).read_text(encoding='utf-8')
    return pd.read_csv(StringIO(csv_content))

# Load all data files
finturk_tables = _load_csv('finturk_tables.csv')
bddk_tables = _load_csv('bddk_tables.csv')
cities = _load_csv('cities.csv')
finturk_groups = _load_csv('finturk_groups.csv')
bddk_groups = _load_csv('bddk_groups.csv')
