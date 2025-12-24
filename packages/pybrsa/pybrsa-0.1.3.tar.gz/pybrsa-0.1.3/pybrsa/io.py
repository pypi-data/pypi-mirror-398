import tempfile
import pandas as pd

def tempfile_base() -> str:
    """
    Create a temporary file base name without extension.

    Equivalent to R's tempfile() function.

    Returns
    -------
    str
        Temporary file path without extension

    Examples
    --------
    >>> temp_path = tempfile_base()
    >>> # Use with save_data
    >>> pybrsa.save_data(df, temp_path, format="csv")
    """
    with tempfile.NamedTemporaryFile() as tmp:
        # Get path and remove any potential extension
        base = tmp.name.rsplit('.', 1)[0] if '.' in tmp.name else tmp.name
        return base


def save_data(
    df: pd.DataFrame,
    filename: str = None,
    format: str = "pkl"
) -> str:
    """
    Save fetched data to multiple formats.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to save
    filename : str
         **Required**. A non-empty string (without extension) must be provided.
    format : str, default "pkl"
        Output format: "pkl", "csv", or "xlsx"

    Returns
    -------
    str
        Full file path with extension

    Examples
    --------
    >>> import pybrsa
    >>> import tempfile

    >>> df = pybrsa.fetch_bddk1(2024, 1, table_no=1)
    >>> temp_path = tempfile_base()
    >>> saved_path = pybrsa.save_data(df, temp_path, format="csv")
    """
    valid_formats = ["pkl", "csv", "xlsx"]
    if format not in valid_formats:
        raise ValueError(
            f"Invalid format. Must be one of: {
                ', '.join(valid_formats)}")
    if filename is None or filename == "":
        raise ValueError("Argument 'filename' is required and cannot be empty")
       
    # Add extension
    filename = f"{filename}.{format}"

    if format == "csv":
        df.to_csv(filename, index=False)
    elif format == "xlsx":
        df.to_excel(filename, index=False)
    elif format == "pkl":
        df.to_pickle(filename)

    print(f"Data saved to {filename}")
    return filename
