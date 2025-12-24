from .data import cities  # ← Relative import (fails in REPL)
#from data import cities  # ← Absolute import (works in REPL)

def plaka_to_city(plaka: Union[int, List[int]]) -> Union[str, List[str]]:
    """
    Convert plaka (license plate number) to province name.
    
    Parameters
    ----------ß
    plaka : int or list of int
        License plate number(s)
    
    Returns
    -------
    str or list of str
        Province name(s) in ALL CAPS
    """
    single_value = False
    if isinstance(plaka, int):
        plaka = [plaka]
        single_value = True
    
    # Load cities data
    cities_df = cities
    
    # Validate plaka codes
    invalid = [p for p in plaka if p not in cities_df["plaka"].values]
    if invalid:
        raise ValueError(
            f"Invalid plaka(s): {invalid}. "
            f"Valid plaka: 0 (HEPSI), 1-81, 999 (YURT DISI)"
        )
    
    # Map plaka to city names
    city_names = []
    for p in plaka:
        city_name = cities_df.loc[cities_df["plaka"] == p, "il"].values
        if len(city_name) > 0:
            city_names.append(city_name[0])
        else:
            city_names.append(None)
    
    return city_names[0] if single_value else city_names



import pandas as pd  
def parse_json(parsed_json: dict) -> pd.DataFrame:
    """
    Parse JSON response from BDDK/Finturk APIs.
    
    Parameters
    ----------
    parsed_json : dict
        The parsed JSON object from API response
    
    Returns
    -------
    pd.DataFrame
        DataFrame with parsed data
    """
    if not parsed_json:
        return pd.DataFrame()
    
    cols_to_keep = list(range(len(parsed_json.get("colModels", []))))
    col_models = parsed_json.get("colModels", [])
    col_labels = parsed_json.get("colNames", [])
    rows = parsed_json.get("data", {}).get("rows", [])
    
    if not rows:
        return pd.DataFrame()
    
    # Determine column names
    final_names = []
    for i in cols_to_keep:
        if i < len(col_labels) and col_labels[i]:
            final_names.append(col_labels[i])
        elif i < len(col_models) and "name" in col_models[i]:
            final_names.append(col_models[i]["name"])
        else:
            final_names.append(f"col_{i}")
    
    # Extract data
    data = {name: [] for name in final_names}
    
    for row in rows:
        cells = row.get("cell", [])
        for i, name in enumerate(final_names):
            value = cells[i] if i < len(cells) else None
            data[name].append(value)
    
    df = pd.DataFrame(data)
    return df
