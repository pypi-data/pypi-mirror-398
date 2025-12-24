import pandas as pd
import requests
import warnings
import time
import re
from typing import Union, List
from .utils import plaka_to_city, parse_json
from .data import cities

def fetch_finturk1(
    year: int,
    month: int,
    table_no: int,
    grup_kod: Union[int, List[int]] = 10001,
    il: Union[int, List[int]] = 0,
    verbose: bool = False  
) -> pd.DataFrame:
    """
    Fetch quarterly data from BDDK Finturk API.
    
    Parameters
    ----------
    year : int
        4-digit year (YYYY)
    month : int
        Month (3, 6, 9, 12 for quarterly data)
    table_no : int
        Table number (1-7)
    grup_kod : int or list of int, default 10001
        Group code(s) (10001-10007)
    il : int or list of int, default 0
        Plate number(s) (0-81; 999 = Yurt Dışı)
    
    Returns
    -------
    pd.DataFrame
        DataFrame with fetched data and fetch_info in attrs

     Examples
    --------
    >>> # Single group, all provinces
    >>> df = fetch_finturk1(2020, 3, 1, grup_kod=10001)
    >>> 'il_adi' in df.columns
    True
    
    >>> # Multiple groups and specific provinces
    >>> df = fetch_finturk1(2020, 3, 1, grup_kod=[10006, 10007], il=[6, 34])
    >>> set(df['grup_kod'].astype(int).unique()) == {10006, 10007}
    True
    
    >>> # Single group, single province
    >>> df = fetch_finturk1(2020, 3, 1, grup_kod=10001, il=34)
    >>> df['il_adi'].iloc[0]
    'İSTANBUL'
    
    See Also
    --------
    fetch_bddk1 : For monthly data without province granularity.              
    """
    if month not in [3, 6, 9, 12]:
        raise ValueError("Finturk requires quarterly months (3, 6, 9, 12)")
    
    if isinstance(grup_kod, int):
        grup_kod = [grup_kod]
    if isinstance(il, int):
        il = [il]
    
    grup_kod = [str(kod) for kod in grup_kod]
    city_names = plaka_to_city(il)
    
    base_url = "https://www.bddk.org.tr/BultenFinturk/tr/Home/VeriGetir"
    
    data = {
        "tabloNo": str(table_no),
        "donem": f"{year}-{month}"
    }
    
    for i, kod in enumerate(grup_kod):
        data[f"tarafList[{i}]"] = kod
    
    for i, city in enumerate(city_names):
        data[f"sehirList[{i}]"] = city
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.bddk.org.tr/BultenFinturk"
    }
    
    try:
        response = requests.post(base_url, data=data, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP error: {e}")
    
    parsed = response.json()
    if not parsed.get("success", False):
        warnings.warn("API reported unsuccessful request")
        return pd.DataFrame()
    
    df = parse_json(parsed.get("Json", {}))

    if df.empty:
        warnings.warn(f"No data for table {table_no}, {year}-{month:02d}")
        return pd.DataFrame()
    
    if "Eftodu" in df.columns:
        df = df.rename(columns={"Eftodu": "grup_kod"})
    

    current_cols = list(df.columns)
    for i, col in enumerate(current_cols):
        if re.fullmatch(r'Şehir', col, re.IGNORECASE):
            current_cols[i] = 'il_adi'
    df.columns = current_cols
    
    city_to_plaka = dict(zip(cities["il"], cities["plaka"]))
    df["plaka"] = df["il_adi"].map(city_to_plaka)
    
    df["grup_kod"] = df["grup_kod"].astype(str)
    df["period"] = f"{year}-{month:02d}"
    df["table_no"] = str(table_no)
    
    # Store fetch info
    df.attrs["fetch_info"] = {
        "start_date": f"{year}-{month:02d}",
        "end_date": f"{year}-{month:02d}",
        "table_no": table_no,
        "grup_kod": grup_kod,
        "il": il,
        "cities": city_names
    }
    
    return df


def fetch_finturk(
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
    table_no: int,
    grup_kod: Union[int, List[int]] = 10001,
    il: Union[int, List[int]] = 0,
    delay: float = 0.5,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Fetch Finturk data for a range of quarters.
    
    Parameters
    ----------
    start_year, end_year : int
        Starting and ending year (YYYY)
    start_month, end_month : int
        Starting and ending month (3, 6, 9, 12)
    table_no : int
        Table number (1-7)
    grup_kod : int or list of int, default 10001
        Group code(s) (10001-10007)
    il : int or list of int, default 0
        Plate number(s) (0-81; 999 = Yurt Dışı)
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
    >>> # Fetch multiple quarters
    >>> my_data = fetch_finturk(2024, 3, 2024, 9, table_no=1)
    >>> len(my_data['period'].unique()) == 3  # 3 quarters: 2024-03, 06, 09
    True
    
    See Also
    --------
    fetch_bddk : For monthly BRSA data.              
    """
    valid_months = [3, 6, 9, 12]
    
    if start_month not in valid_months or end_month not in valid_months:
        raise ValueError("Start and end months must be one of 3, 6, 9, 12 (quarterly)")
    
    periods = []
    for year in range(start_year, end_year + 1):
        for month in valid_months:
            if year == start_year and month < start_month:
                continue
            if year == end_year and month > end_month:
                continue
            periods.append({"year": year, "month": month})
    
    if verbose:
        print(
            f"Fetching table {table_no} for {len(periods)} quarterly periods: "
            f"{start_year}-{start_month:02d} to {end_year}-{end_month:02d}"
        )
    
    results = []
    errors = []
    
    for i, period in enumerate(periods, 1):
        year = period["year"]
        month = period["month"]
        
        if verbose:
            print(f"[{i}/{len(periods)}] {year}-{month:02d}... ", end="", flush=True)
        
        try:
            df_period = fetch_finturk1(year, month, table_no, grup_kod, il)
            
            if not df_period.empty:
                results.append(df_period)
                if verbose:
                    print(f"{len(df_period)} rows")
            else:
                if verbose:
                    print("No data")
                    
        except Exception as e:
            if verbose:
                print(f"Error: {e}")
            errors.append({"year": year, "month": month, "error": str(e)})
        
        if i < len(periods) and delay > 0:
            time.sleep(delay)
    
    if not results:
        warnings.warn("No data retrieved")
        return pd.DataFrame()
    
    combined_df = pd.concat(results, ignore_index=True)
    
    # Store fetch info
    combined_df.attrs["fetch_info"] = {
        "start_date": f"{start_year}-{start_month:02d}",
        "end_date": f"{end_year}-{end_month:02d}",
        "table_no": table_no,
        "grup_kod": grup_kod,
        "il": il,
        "errors": errors
    }
    
    return combined_df