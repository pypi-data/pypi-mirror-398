
# `pybrsa`: A Python Package for Turkish Banking Sector Data

[![PyPI version](https://img.shields.io/pypi/v/pybrsa)](https://pypi.org/project/pybrsa/)
[![Documentation](https://img.shields.io/badge/docs-GitHub_Pages-blue)](https://obakis.github.io/pybrsa/)

A Python package for programmatic access to Turkish banking sector data from the [Turkish Banking Regulation and Supervision Agency](https://www.bddk.org.tr) (BRSA, known as BDDK in Turkish). The package provides Python users with a clean interface to fetch monthly and quarterly banking statistics, financial reports, and sectoral indicators directly from BRSA's official APIs. Specifically, the package retrieves tables from two distinct publication portals maintained by the BRSA:

- The [Monthly Bulletin Portal](https://www.bddk.org.tr/bultenaylik/){.uri} 
- The [FinTurk Data System](https://www.bddk.org.tr/bultenfinTurk/){.uri} 

## Key Features

- Direct API access to BRSA monthly bulletins (17 financial tables)
- Quarterly FinTurk data with city-level granularity (7 tables, 82 cities including 'HEPSI' for all cities)
- Consistent parameter interface for both data sources
- Built-in metadata for tables, banking groups, and provinces
- Multiple export formats: CSV, Excel via `save_data()`
- Returns pandas DataFrames ready for analysis

## Design Philosophy

**Lightweight and Authentic:** Other packages providing access to BDDK data also fetch data programmatically, but they add a heavy translation layer - maintaining manual configuration files to map Turkish column names and categorical values to English. This provides user convenience at a high maintenance cost.

`pybrsa` takes a different path. It interacts directly with the API and uses the data it returns with minimal alteration:

- For the **Monthly Bulletin**, it uses the **official English column names and labels** provided by the API when `lang = "en"` is set.
- For the **FinTurk dataset**, where the API provides data only in Turkish, it returns the **authentic Turkish names**.

**This is a deliberate choice.** By avoiding a separate translation file, `pybrsa` eliminates a major maintenance burden, aiming to adapt instantly to any API changes. This way, the data you see is exactly what the official source provides.

## Related Packages

- [bddk](https://github.com/barbasan/bddk){.uri}  (Python): Uses manual
  configuration for translations and column mappings and provides access
  only to the Monthly Bulletin.
- [bddkdata](https://github.com/urazakgul/bddkdata){.uri}  (Python): Provides
  similar functionality for Python/pandas users with the same
  constraints as bddk.  
- [rbrsa](https://github.com/obakis/pybrsa){.uri}  R companion to this package with consistent API.
- [bddkR](https://github.com/ozancanozdemir/bddkR){.uri}  (R): Uses manual
  configuration for translations and column mappings and provides access
  only to the Monthly Bulletin. It is based on 'bddkdata'




## Installation

Install from PyPI:

```bash
pip install pybrsa
```

The development version can be installed from GitHub:

``` bash
pip install git+https://github.com/obakis/pybrsa.git
```

## Getting started

*A vignette demonstrating how to use main functions, download and save
data from both BDDK and FinTurk interface can be found at*:
<https://obakis.github.io/pybrsa/articles/introduction.html>

The `pybrsa` package retrieves tables from two distinct publication
portalsmaintained by the Turkish Banking Regulation and Supervision
Agency (BDDK). Both portals are official sources, but they organize the
data differently:

- The [Monthly Bulletin Portal](https://www.bddk.org.tr/bultenaylik/)
  provides high-level, summary reports designed for general consumption
  and quick overviews of monthly trends without any geographic coverage.
- The [FinTurk Data System](https://www.bddk.org.tr/BultenFinTurk/)
  provides granular, detailed data, including statistics broken down by
  province, whereas the standard Monthly Bulletin offers national-level
  aggregates.

``` python
## R users: to use list_tables() as in R you can do
# from pybrsa import list_tables, fetch_bddk
## or importing everything
# from pybrsa import * 

import pybrsa

# Explore available tables
pybrsa.list_tables("bddk")  # For English names
pybrsa.list_tables("bddk", "tr")  # For Turkish names
pybrsa.list_tables("finturk")

# Explore banking groups
pybrsa.list_groups("bddk")
pybrsa.list_groups("bddk", "tr")
pybrsa.list_groups("finturk")

# Fetch monthly data (Table 15: Ratios)
data = pybrsa.fetch_bddk(
    start_year=2024, start_month=1,
    end_year=2024, end_month=3,
    table_no=15, grup_kod=10001
)

# Fetch quarterly FinTurk data
q_data = pybrsa.fetch_finturk(
    start_year=2024, start_quarter=3,
    end_year=2024, end_quarter=9,
    table_no=1, grup_kod=10007
)

# Save results to CSV
# q_data.to_csv("my_file.csv", index=False)
temp_path = pybrsa.tempfile_base()
pybrsa.save_data(q_data, "temp_path", format="csv")
```
