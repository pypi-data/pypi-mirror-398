import requests
import pandas as pd
import json
import time
from typing import Union, List, Optional
from datetime import datetime, timedelta
import warnings
from .utils import parse_json


def fetch_bddk1(
    year: int, 
    month: int, 
    table_no: int, 
    grup_kod: Union[int, List[int]] = 10001,
    currency: str = "TL", 
    lang: str = "en",
    verbose: bool = False
) -> pd.DataFrame:
    """
    Fetch monthly data from BDDK API.
    
    Parameters
    ----------
    year : int
        4-digit year (YYYY)
    month : int
        Month (1-12)
    table_no : int
        Table number (1-17)
    grup_kod : int or list of int, default 10001
        Group code(s) (10001-10010)
    currency : str, default "TL"
        Currency code ("TL" or "USD")
    lang : str, default "en"
        Language ("en" or "tr")
    
    Returns
    -------
    pd.DataFrame
        DataFrame with fetched data and fetch_info in attrs

    Examples
    --------
    >>> # Single group code
    >>> df = fetch_bddk1(2020, 3, 1, grup_kod=10001)
    >>> df.shape
    (82, 12)
    
    >>> # Multiple group codes
    >>> df = fetch_bddk1(2020, 3, 1, grup_kod=[10001, 10002])
    >>> len(df['grup_kod'].unique())
    2
    
    >>> # Turkish language output
    >>> df = fetch_bddk1(2020, 3, 1, grup_kod=10001, lang="tr")
    >>> 'Yıl' in df.columns  # Turkish column names
    True
    
    See Also
    --------
    fetch_finturk1 : For quarterly province-level data.        
    """
    base_url = f"https://www.bddk.org.tr/BultenAylik/{lang}/Home/BasitRaporGetir"
    
    params = [
        ("tabloNo", str(table_no)),
        ("yil", str(year)),
        ("ay", str(month)),
        ("paraBirimi", currency)
    ]
    
    # Handle single or multiple grup_kod
    if isinstance(grup_kod, int):
        grup_kod = [grup_kod]
    
    for kod in grup_kod:
        params.append(("taraf", str(kod)))  
    
    try:
        response = requests.post(base_url, data=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP error: {e}")
    
    parsed = response.json()
    if not parsed.get("success", False):
        raise Exception("API reported unsuccessful request")
    
    df = parse_json(parsed.get("Json", {}))
    
    if df.empty:
        warnings.warn(
            f"No data for table {table_no}, {year}-{month:02d}, "
            f"grup_kod {grup_kod}"
        )
        return pd.DataFrame()
    
    if len(df.columns) > 0:
        df = df.rename(columns={df.columns[0]: "group_name"})
    
    df = df.reset_index(drop=True)
    group_rle = []
    current_name = None
    count = 0
    
    for name in df["group_name"]:
        if name != current_name:
            if current_name is not None:
                group_rle.append((current_name, count))
            current_name = name
            count = 1
        else:
            count += 1
    
    if current_name is not None:
        group_rle.append((current_name, count))
    
    grup_kod_series = []
    for i, (name, length) in enumerate(group_rle):
        kod = grup_kod[i % len(grup_kod)] if len(grup_kod) > i else grup_kod[-1]
        grup_kod_series.extend([kod] * length)
    
    df["grup_kod"] = grup_kod_series
    df["period"] = f"{year}-{month:02d}"
    df["currency"] = currency
    
    # Store fetch info in DataFrame attributes
    df.attrs["fetch_info"] = {
        "start_date": f"{year}-{month:02d}",
        "end_date": f"{year}-{month:02d}",
        "table_no": table_no,
        "currency": currency,
        "grup_kod": grup_kod,
        "lang": lang
    }
    
    return df


def fetch_bddk(
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
    table_no: int,
    grup_kod: Union[int, List[int]] = 10001,
    currency: str = "TL",
    lang: str = "en",
    delay: float = 0.5,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Fetch BDDK data for a range of months.
    
    Parameters
    ----------
    start_year, end_year : int
        Starting and ending year (YYYY)
    start_month, end_month : int
        Starting and ending month (1-12)
    table_no : int
        Table number (1-17)
    grup_kod : int or list of int, default 10001
        Group code(s) (10001-10010)
    currency : str, default "TL"
        Currency code ("TL" or "USD")
    lang : str, default "en"
        Language ("en" or "tr")
    delay : float, default 0.5
        Delay between requests in seconds
    verbose : bool, default True
        Print progress messages
    
    Returns
    -------
    pd.DataFrame
        Combined DataFrame with fetch_info in attrs

     Examples
    --------
    >>> # Fetch multiple months
    >>> my_dat = fetch_bddk(2024, 1, 2024, 3, table_no=15)
    >>> my_dat.shape[0] > 0
    True
    
    See Also
    --------
    fetch_finturk : For quarterly province-level data.              
    """
    start_date = datetime(start_year, start_month, 1)
    end_date = datetime(end_year, end_month, 1)
    
    if start_date > end_date:
        raise ValueError("Start date must be before or equal to end date")
    
    month_dates = []
    current = start_date
    while current <= end_date:
        month_dates.append(current)
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
    
    if verbose:
        print(
            f"Fetching table {table_no} for {len(month_dates)} months: "
            f"{start_date.strftime('%Y-%m')} to {end_date.strftime('%Y-%m')}"
        )
    
    results = []
    errors = []
    
    for i, month_date in enumerate(month_dates, 1):
        year = month_date.year
        month = month_date.month
        
        if verbose:
            print(f"[{i}/{len(month_dates)}] {year}-{month:02d}... ", end="", flush=True)
        
        try:
            df_month = fetch_bddk1(year, month, table_no, grup_kod, currency, lang)
            
            if not df_month.empty:
                results.append(df_month)
                if verbose:
                    print(f"{len(df_month)} rows")
            else:
                if verbose:
                    print("No data")
                    
        except Exception as e:
            if verbose:
                print(f"Error: {e}")
            errors.append({"year": year, "month": month, "error": str(e)})
        
        if i < len(month_dates) and delay > 0:
            time.sleep(delay)
    
    if not results:
        warnings.warn("No data was successfully retrieved")
        return pd.DataFrame()
    
    combined_df = pd.concat(results, ignore_index=True)
    
    # Store fetch info in DataFrame attributes
    combined_df.attrs["fetch_info"] = {
        "start_date": start_date.strftime("%Y-%m"),
        "end_date": end_date.strftime("%Y-%m"),
        "table_no": table_no,
        "currency": currency,
        "grup_kod": grup_kod,
        "lang": lang,
        "errors": errors
    }
    
    return combined_df