
# pybrsa: A Python Package for Turkish Banking Sector Data

[![PyPI version](https://img.shields.io/pypi/v/pybrsa)](https://pypi.org/project/pybrsa/)
[![Documentation](https://img.shields.io/badge/docs-GitHub_Pages-blue)](https://obakis.github.io/pybrsa/)

A Python package for programmatic access to Turkish banking sector data from the [Turkish Banking Regulation and Supervision Agency](https://www.bddk.org.tr) (BRSA, known as BDDK in Turkish). The package provides Python users with a clean interface to fetch monthly and quarterly banking statistics, financial reports, and sectoral indicators directly from BRSA's official APIs. Specifically, the package retrieves tables from two distinct publication portals maintained by the BRSA:

- The [Monthly Bulletin Portal](https://www.bddk.org.tr/bultenaylik/)
- The [FinTurk Data System](https://www.bddk.org.tr/BultenFinTurk/)

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

- [bddk](https://github.com/barbasan/bddk) (Python): Uses manual
  configuration for translations and column mappings and provides access
  only to the Monthly Bulletin.
- [bddkdata](https://github.com/urazakgul/bddkdata) (Python): Provides
  similar functionality for Python/pandas users with the same
  constraints as bddk.  
- [rbrsa](https://github.com/obakis/pybrsa) R companion to this package with consistent API.
- [bddkR](https://github.com/ozancanozdemir/bddkR) (R): Uses manual
  configuration for translations and column mappings and provides access
  only to the Monthly Bulletin. It is based on 'bddkdata'


## Key Changes Made:
1. **Header**: Changed to Python badges (PyPI version and GitHub Pages docs)
2. **Installation**: Updated from R's `install.packages()` to Python's `pip install`
3. **Code Examples**: Completely rewritten in Python syntax with `import pybrsa`
4. **Functions**: Adapted R function calls to Python style (e.g., `pybrsa.list_tables()`)
5. **Data Export**: Changed RDS to CSV and added pandas DataFrame export methods
6. **File Reference**: Removed the RMarkdown note at the top since this is a direct `.md` file
7. **Structure**: Kept your original sections but updated all content for Python users

**Next Step**: Replace your current `README.md` file with this content. Once that's done and pushed to GitHub, we can move on to the next single step: preparing for PyPI upload.

## Installation

Install from PyPI:

```bash
pip install pybrsa
```

The development version can be installed from GitHub:

``` r
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
q_data.to_csv("finturk_data.csv", index=False)

# Or use the save_data function for multiple formats
pybrsa.save_data(q_data, "finturk_data", format="csv")

```
