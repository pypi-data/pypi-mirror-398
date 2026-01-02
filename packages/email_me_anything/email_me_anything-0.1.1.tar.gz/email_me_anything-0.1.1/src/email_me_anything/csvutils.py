"""
CSV utilities for reading and processing CSV files.
"""
import csv
import random
from pathlib import Path 
from typing import Any, Dict, List

def read_csv(filepath: Path) -> List[List[str]] | None:
    """
    Read a CSV file and return its contents as a list of rows.
    Args:
        filepath (Path): The file path to the CSV file to read.
    Returns:
        List[List[str]] | None: A list of rows, where each row is a list of strings
                                representing the CSV columns. Returns None if an error
                                occurs during file reading.
    Raises:
        No exceptions are raised; errors are caught and printed to stdout.
    Example:
        >>> rows = read_csv(Path('data.csv'))
        >>> if rows:
        ...     print(f"Read {len(rows)} rows from CSV")
    """
    
    try:
        with open(filepath, mode='r', encoding='utf-8') as file:
            return [row for row in csv.reader(file)]
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

def convert_row_to_dict(row : List[str], headers: List[str]=None) -> Dict[str, Any]:
    """
    Convert a row of data into a dictionary.
    If headers are provided, uses them as keys and maps each header to the 
    corresponding value in the row. If a row has fewer values than headers,
    missing values are filled with empty strings.
    If no headers are provided, generates default column names (col0, col1, etc.)
    as keys.
    Args:
        row (List[str]): A list of string values representing a data row.
        headers (List[str], optional): A list of header names to use as dictionary keys.
                                       If None, auto-generated column names are used.
                                       Defaults to None.
    Returns:
        Dict[str, Any]: A dictionary mapping header/column names to row values.
    Examples:
        >>> convert_row_to_dict(['Alice', '25', 'NYC'], ['name', 'age', 'city'])
        {'name': 'Alice', 'age': '25', 'city': 'NYC'}
        >>> convert_row_to_dict(['Bob', '30'], ['name', 'age', 'city'])
        {'name': 'Bob', 'age': '30', 'city': ''}
        >>> convert_row_to_dict(['Charlie', '35', 'LA'])
        {'col0': 'Charlie', 'col1': '35', 'col2': 'LA'}
    """
    
    if headers:
        return {key: row[idx] if idx < len(row) else "" for idx, key in enumerate(headers)}
    else:
        return {f"col{idx}": val for idx, val in enumerate(row)}

def select_random_row(csv_path: Path, skip_header: bool=True) -> Dict[str, Any] | None:
    """
    Select a random row from a CSV file and return it as a dictionary.
    Args:
        csv_path (Path): The file path to the CSV file to read.
        skip_header (bool, optional): Whether to skip the first row as a header. 
                                      Defaults to True.
    Returns:
        Dict[str, Any] | None | bool: A dictionary representing the randomly selected row on success.
            Returns False if the CSV could not be read (for example, file access error).
            Returns None if the CSV exists but contains no data rows (only a header or empty).

    Raises:
        None explicitly, but may raise exceptions from `read_csv()` or `convert_row_to_dict()`.
    Example:
        >>> row = select_random_row(Path("data.csv"))
        >>> print(row)
        {'name': 'John', 'age': '30', 'email': 'john@example.com'}
    """
    
    table = read_csv(csv_path)
    if not table:
        print("No data found in CSV.")
        return False
    start = 1 if skip_header else 0
    if len(table) <= start:
        return None
    return convert_row_to_dict(table[random.randint(start, len(table) - 1)], headers=table[0] if skip_header else None)
