import pandas as pd
from .data import cities, bddk_groups, finturk_groups, bddk_tables, finturk_tables


def list_cities() -> pd.DataFrame:
    """
    List available cities for Finturk quarterly data with plaka numbers.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns 'plaka' and 'il'

    Examples
    --------
    >>> import pybrsa
    >>> df = pybrsa.list_cities()
    >>> print(df.head())
    """
    print("\nAvailable cities for Finturk quarterly data")
    print("Use license plate number (plaka) in fetch_finturk functions:")
    print("Valid values: 0 (HEPSI/ALL), 1-81, 999 (YURT DISI/ABROAD)\n")


    df = cities[['plaka', 'il']].copy()
    print(df.to_string(index=False))

    return df


def list_groups(source: str = "bddk", lang: str = "en") -> pd.DataFrame:
    """
    List available banking groups for a data source.

    Parameters
    ----------
    source : str, default "bddk"
        Either "bddk" or "finturk"
    lang : str, default "en"
        Either "tr" or "en" for names

    Returns
    -------
    pd.DataFrame
        DataFrame with columns 'Group_Code' and 'Name'

    Examples
    --------
    >>> import pybrsa
    >>> df = pybrsa.list_groups("bddk")
    >>> df = pybrsa.list_groups("finturk", "tr")
    """
    source = source.lower()
    lang = lang.lower()

    if source not in ["bddk", "finturk"]:
        raise ValueError("source must be either 'bddk' or 'finturk'")
    if lang not in ["en", "tr"]:
        raise ValueError("lang must be either 'en' or 'tr'")

    if source == "bddk":
        groups = bddk_groups
        name_col = "name_tr" if lang == "tr" else "name_en"
    else:  # finturk
        groups = finturk_groups
        name_col = "name_tr" if lang == "tr" else "name_en"

    df = groups[['grup_kod', name_col]].copy()
    df.columns = ['Group_Code', 'Name']

    print(f"\nAvailable banking groups for {source} data:\n")
    print(df.to_string(index=False))

    return df


def list_tables(source: str = "bddk", lang: str = "en") -> pd.DataFrame:
    """
    List available tables for a data source.

    Parameters
    ----------
    source : str, default "bddk"
        Either "bddk" or "finturk"
    lang : str, default "en"
        Either "tr" or "en" for table titles

    Returns
    -------
    pd.DataFrame
        DataFrame with columns 'Table_No' and 'Title'

    Examples
    --------
    >>> import pybrsa
    >>> df = pybrsa.list_tables("bddk")
    >>> df = pybrsa.list_tables("finturk", "tr")
    """
    source = source.lower()
    lang = lang.lower()

    if source not in ["bddk", "finturk"]:
        raise ValueError("source must be either 'bddk' or 'finturk'")
    if lang not in ["en", "tr"]:
        raise ValueError("lang must be either 'en' or 'tr'")

    if source == "bddk":
        tables = bddk_tables
        title_col = "title_tr" if lang == "tr" else "title_en"
    else:  # finturk
        tables = finturk_tables
        title_col = "title_tr" if lang == "tr" else "title_en"

    df = tables[['table_no', title_col]].copy()
    df.columns = ['Table_No', 'Title']

    print(f"\nAvailable tables for {source} data:\n")
    print(df.to_string(index=False))

    return df
