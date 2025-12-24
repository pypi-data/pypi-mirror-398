import pandas as pd
import os

# Get the directory where data.py is located
_current_dir = os.path.dirname(os.path.abspath(__file__))
_data_dir = os.path.join(_current_dir, 'data')

# Load CSVs
finturk_tables = pd.read_csv(os.path.join(_data_dir, 'finturk_tables.csv'))
bddk_tables = pd.read_csv(os.path.join(_data_dir, 'bddk_tables.csv'))
cities = pd.read_csv(os.path.join(_data_dir, 'cities.csv'))
finturk_groups = pd.read_csv(os.path.join(_data_dir, 'finturk_groups.csv'))
bddk_groups = pd.read_csv(os.path.join(_data_dir, 'bddk_groups.csv'))